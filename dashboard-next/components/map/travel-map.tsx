"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { OptimizeResponse } from "@/lib/types";
import { LeagueTheme } from "@/lib/league-theme";
import { getTeamMeta } from "@/lib/team-meta";

interface TravelMapProps {
  data: OptimizeResponse;
  highlightedTeam?: string | null;
  theme: LeagueTheme;
}

export function TravelMap({ data, highlightedTeam, theme }: TravelMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<maplibregl.Map | null>(null);
  const [isMapReady, setIsMapReady] = useState(false);
  const teamMetrics = useMemo(() => new Map(data.team_metrics.map((t) => [t.team, t])), [data.team_metrics]);
  const homeDatesByTeam = useMemo(() => {
    const map = new Map<string, string[]>();
    for (const g of data.schedule) {
      const dates = map.get(g.home) ?? [];
      dates.push(g.date);
      map.set(g.home, dates);
    }
    return map;
  }, [data.schedule]);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;
    const rasterStyle: maplibregl.StyleSpecification = {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution: "© OpenStreetMap contributors"
        }
      },
      layers: [{ id: "osm", type: "raster", source: "osm" }]
    };

    const map = new maplibregl.Map({
      container: mapRef.current,
      style: rasterStyle,
      center: [-98.5795, 39.8283],
      zoom: data.meta.league === "NHL" ? 2.3 : 3.1
    });

    mapInstanceRef.current = map;
    map.on("load", () => setIsMapReady(true));
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    return () => {
      setIsMapReady(false);
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [data.meta.league]);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !isMapReady || !map.isStyleLoaded()) return;

    const features = data.team_locations.map((loc) => {
      const metric = teamMetrics.get(loc.team);
      return {
        type: "Feature",
        properties: {
          team: loc.team,
          emissions: metric?.emissions_kg ?? 0,
          distance: metric?.distance_miles ?? 0,
          highlighted: highlightedTeam && loc.team === highlightedTeam ? 1 : 0
        },
        geometry: {
          type: "Point",
          coordinates: [loc.longitude, loc.latitude]
        }
      };
    });

    const geojson = { type: "FeatureCollection", features } as GeoJSON.FeatureCollection;

    if (map.getSource("teams")) {
      (map.getSource("teams") as maplibregl.GeoJSONSource).setData(geojson);
    } else {
      map.addSource("teams", { type: "geojson", data: geojson });

      if (!map.getLayer("emissions-heat")) {
        map.addLayer({
          id: "emissions-heat",
          type: "heatmap",
          source: "teams",
          maxzoom: 8,
          paint: {
            "heatmap-weight": ["interpolate", ["linear"], ["get", "emissions"], 0, 0, 800000, 1],
            "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 0.8, 9, 2],
            "heatmap-color": [
              "interpolate",
              ["linear"],
              ["heatmap-density"],
              0,
              "rgba(0,0,0,0)",
              0.3,
              theme.map.heat[0],
              0.6,
              theme.map.heat[1],
              1,
              theme.map.heat[2]
            ]
          }
        });
      }

      if (!map.getLayer("team-points")) {
        map.addLayer({
          id: "team-points",
          type: "circle",
          source: "teams",
          paint: {
            "circle-radius": ["case", ["==", ["get", "highlighted"], 1], 9, 6],
            "circle-color": ["case", ["==", ["get", "highlighted"], 1], theme.map.markerHighlight, theme.map.marker],
            "circle-stroke-color": "#0f172a",
            "circle-stroke-width": 1.5
          }
        });
      }

      if (!(map as unknown as { __teamClickBound?: boolean }).__teamClickBound) {
        map.on("click", "team-points", (evt) => {
          const feature = evt.features?.[0];
          if (!feature) return;
          const props = feature.properties as Record<string, string>;
          const meta = getTeamMeta(props.team, data.meta.league);
          const clickTeam = props.team;
          const visitDates = highlightedTeam
            ? data.schedule
                .filter((g) => g.home === clickTeam && g.away === highlightedTeam)
                .map((g) => g.date)
                .sort()
            : [];
          const dates = (highlightedTeam ? visitDates : homeDatesByTeam.get(clickTeam) ?? []).slice(0, 12);
          const extra = Math.max(0, (highlightedTeam ? visitDates.length : homeDatesByTeam.get(clickTeam)?.length ?? 0) - dates.length);
          const label = highlightedTeam ? `Visit dates for ${highlightedTeam}` : "Home dates";
          const dateHtml = dates.length
            ? `<br/>${label}: ${dates.join(", ")}${extra ? `, +${extra} more` : ""}`
            : `<br/>${label}: none`;
          new maplibregl.Popup({ offset: 12 })
            .setLngLat((feature.geometry as GeoJSON.Point).coordinates as [number, number])
            .setHTML(
              `<div style="font-size:12px"><strong>${props.team}</strong><br/>City: ${meta.city}<br/>Emissions: ${Number(
                props.emissions
              ).toLocaleString()} kg<br/>Distance: ${Number(props.distance).toLocaleString()} mi${dateHtml}</div>`
            )
            .addTo(map);
        });
        (map as unknown as { __teamClickBound?: boolean }).__teamClickBound = true;
      }
    }

    const locByTeam = new Map(data.team_locations.map((l) => [l.team, l]));
    const routePoints =
      highlightedTeam == null
        ? []
        : data.schedule
            .filter((g) => g.home === highlightedTeam || g.away === highlightedTeam)
            .slice(0, 80)
            .map((g) => locByTeam.get(g.home))
            .filter(Boolean)
            .map((l) => [l!.longitude, l!.latitude]);

    const routeData = {
      type: "FeatureCollection",
      features:
        routePoints.length > 1
          ? [
              {
                type: "Feature",
                properties: {},
                geometry: { type: "LineString", coordinates: routePoints }
              }
            ]
          : []
    } as GeoJSON.FeatureCollection;

    if (map.getSource("routes")) {
      (map.getSource("routes") as maplibregl.GeoJSONSource).setData(routeData);
    } else {
      map.addSource("routes", { type: "geojson", data: routeData });
      if (!map.getLayer("team-routes")) {
        map.addLayer({
          id: "team-routes",
          type: "line",
          source: "routes",
          paint: {
            "line-color": theme.map.route,
            "line-width": 2.5,
            "line-opacity": 0.75
          }
        });
      }
    }
  }, [data, highlightedTeam, homeDatesByTeam, isMapReady, teamMetrics, theme]);

  return <div ref={mapRef} className={`h-[420px] w-full overflow-hidden rounded-xl ${theme.borderClass}`} aria-label="Travel map" />;
}
