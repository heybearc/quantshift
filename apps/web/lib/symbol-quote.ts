import { normalizeSymbol } from "./user-desk";

export type SymbolQuote = {
  symbol: string;
  price: string;
  bid: string;
  ask: string;
  asOf: string;
  source: "coinbase" | "yahoo";
};

type FetchLike = typeof fetch;

export function isCryptoPair(symbol: string): boolean {
  return symbol.includes("-");
}

function printPrice(value: unknown): string {
  const number = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(number) || number < 0) return "";
  const places = number >= 1 ? 2 : 6;
  return number.toFixed(places);
}

export function parseCoinbaseTicker(body: unknown, symbol: string): SymbolQuote {
  const row = body && typeof body === "object" ? (body as Record<string, unknown>) : {};
  const price = printPrice(row.price);
  if (!price) throw new Error("No quote for that symbol.");
  const asOf = typeof row.time === "string" && row.time ? row.time : new Date().toISOString();
  return {
    symbol,
    price,
    bid: printPrice(row.bid),
    ask: printPrice(row.ask),
    asOf,
    source: "coinbase",
  };
}

export function parseYahooChart(body: unknown, symbol: string): SymbolQuote {
  const chart = body && typeof body === "object" ? (body as { chart?: { result?: Array<{ meta?: Record<string, unknown> }> } }).chart : undefined;
  const meta = chart?.result?.[0]?.meta;
  const price = printPrice(meta?.regularMarketPrice);
  if (!price) throw new Error("No quote for that symbol.");
  const seconds = Number(meta?.regularMarketTime);
  const asOf = Number.isFinite(seconds) && seconds > 0 ? new Date(seconds * 1000).toISOString() : new Date().toISOString();
  return {
    symbol,
    price,
    bid: printPrice(meta?.bid),
    ask: printPrice(meta?.ask),
    asOf,
    source: "yahoo",
  };
}

export async function readQuote(symbol: string, fetchImpl: FetchLike = fetch): Promise<SymbolQuote> {
  const name = normalizeSymbol(symbol);
  if (!name) throw new Error("Enter a symbol such as NVDA or BTC-USD.");
  if (isCryptoPair(name)) {
    const response = await fetchImpl(`https://api.exchange.coinbase.com/products/${encodeURIComponent(name)}/ticker`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) throw new Error("No quote for that symbol.");
    return parseCoinbaseTicker(await response.json(), name);
  }
  const response = await fetchImpl(
    `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(name)}?interval=1m&range=1d`,
    { headers: { Accept: "application/json", "User-Agent": "QuantShift" }, cache: "no-store" },
  );
  if (!response.ok) throw new Error("No quote for that symbol.");
  return parseYahooChart(await response.json(), name);
}
