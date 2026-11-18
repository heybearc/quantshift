const SYMBOL = /^[A-Z0-9][A-Z0-9.\-]{0,14}$/;

export const BROKERS = [
  { id: "alpaca", name: "Alpaca", adapter: "ready" },
  { id: "coinbase", name: "Coinbase", adapter: "ready" },
  { id: "kraken", name: "Kraken", adapter: "ready" },
  { id: "schwab", name: "Charles Schwab", adapter: "needed" },
  { id: "ibkr", name: "Interactive Brokers", adapter: "needed" },
  { id: "tradier", name: "Tradier", adapter: "needed" },
] as const;

export const PERSONAL_VENUES = BROKERS.filter((broker) => broker.adapter === "ready").map((broker) => broker.id);

export function venueSlug(name: string): string {
  const slug = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length < 2 || slug.length > 32) return "";
  return slug;
}

export function describeBot(name: string) {
  const direct = BROKERS.find((broker) => broker.id === name);
  const slug = direct ? direct.id : venueSlug(name);
  const known = direct || BROKERS.find((broker) => broker.id === slug);
  const adapter = known?.adapter || "needed";
  return {
    venue: slug,
    displayName: known?.name || name.trim(),
    status: adapter === "ready" ? "stopped" : "needs_adapter",
    tradingMode: "paper",
    adapter,
    paperAvailable: true,
  };
}

export function normalizeSymbol(value: string): string {
  const cleaned = value.trim().toUpperCase();
  return SYMBOL.test(cleaned) ? cleaned : "";
}

export function cleanText(value: unknown, limit: number): string {
  if (typeof value !== "string") return "";
  return value.trim().slice(0, limit);
}
