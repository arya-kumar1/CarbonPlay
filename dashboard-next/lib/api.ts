import { OptimizePayload, OptimizeResponse } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_SCHEDULER_API_BASE ?? "http://127.0.0.1:8000";

export async function optimizeSchedule(payload: OptimizePayload): Promise<OptimizeResponse> {
  const res = await fetch(`${API_BASE}/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Optimize request failed (${res.status}): ${text}`);
  }

  return (await res.json()) as OptimizeResponse;
}
