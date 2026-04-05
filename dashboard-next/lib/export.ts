export function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadCsv<T extends object>(filename: string, rows: T[]) {
  if (!rows.length) return;
  const headers = Object.keys(rows[0]) as Array<keyof T>;
  const csv = [
    headers.map((h) => String(h)).join(","),
    ...rows.map((row) => headers.map((h) => JSON.stringify(row[h] ?? "")).join(","))
  ].join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
