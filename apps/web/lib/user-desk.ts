const SYMBOL = /^[A-Z0-9][A-Z0-9.\-]{0,14}$/;

export const PERSONAL_VENUES = ["alpaca", "coinbase", "kraken"] as const;

export function normalizeSymbol(value: string): string {
  const cleaned = value.trim().toUpperCase();
  return SYMBOL.test(cleaned) ? cleaned : "";
}

export function cleanText(value: unknown, limit: number): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, limit);
}
