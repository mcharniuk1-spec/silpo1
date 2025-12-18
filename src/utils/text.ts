export function cleanSpaces(s: string): string {
  return s.replace(/\s+/g, " ").replace(/[\r\n\t]/g, " ").trim();
}

export function toNum(s: string): number {
  return Number(String(s).replace(",", "."));
}

export function safeJoin(parts: Array<string | number | null | undefined>, sep = " "): string {
  return cleanSpaces(
    parts
      .map((p) => (p === null || p === undefined ? "" : String(p)))
      .filter(Boolean)
      .join(sep)
  );
}
