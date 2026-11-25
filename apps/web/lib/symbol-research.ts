import { isCryptoPair } from "./symbol-quote";
import { normalizeSymbol } from "./user-desk";

export type Headline = {
  title: string;
  publisher: string;
  link: string;
  published: string;
};

export type ResearchBrief = {
  symbol: string;
  direction: "rising" | "falling" | "flat";
  last: string;
  dayChange: number | null;
  weekChange: number | null;
  monthChange: number | null;
  high: string;
  low: string;
  volumeRatio: number | null;
  headlines: Headline[];
  trendNote: string;
  newsNote: string;
};

type FetchLike = typeof fetch;

function price(value: unknown): string {
  const number = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(number) || number < 0) return "";
  return number >= 1 ? number.toFixed(2) : number.toFixed(6);
}

function change(last: number, base: number | undefined): number | null {
  if (base == null || !Number.isFinite(base) || base === 0) return null;
  return (last - base) / base;
}

export function closesFromYahooChart(body: unknown): { closes: number[]; volumes: number[] } {
  const result = body && typeof body === "object"
    ? (body as { chart?: { result?: Array<{ indicators?: { quote?: Array<{ close?: Array<number | null>; volume?: Array<number | null> }> } }> } }).chart?.result?.[0]
    : undefined;
  const quote = result?.indicators?.quote?.[0];
  const closes: number[] = [];
  const volumes: number[] = [];
  (quote?.close || []).forEach((close, index) => {
    if (typeof close !== "number" || !Number.isFinite(close)) return;
    closes.push(close);
    const volume = quote?.volume?.[index];
    volumes.push(typeof volume === "number" && Number.isFinite(volume) ? volume : 0);
  });
  return { closes, volumes };
}

export function closesFromCoinbaseCandles(body: unknown): { closes: number[]; volumes: number[] } {
  if (!Array.isArray(body)) return { closes: [], volumes: [] };
  const rows = body
    .filter((row) => Array.isArray(row) && typeof row[0] === "number" && typeof row[4] === "number")
    .slice()
    .sort((a, b) => Number(a[0]) - Number(b[0]));
  return {
    closes: rows.map((row) => Number(row[4])),
    volumes: rows.map((row) => Number(row[5]) || 0),
  };
}

export function parseHeadlines(body: unknown): Headline[] {
  const news = body && typeof body === "object" ? (body as { news?: unknown[] }).news : undefined;
  if (!Array.isArray(news)) return [];
  const headlines: Headline[] = [];
  for (const item of news) {
    if (!item || typeof item !== "object") continue;
    const row = item as Record<string, unknown>;
    const title = typeof row.title === "string" ? row.title.trim() : "";
    const link = typeof row.link === "string" ? row.link.trim() : "";
    if (!title || !/^https:\/\//.test(link)) continue;
    const seconds = Number(row.providerPublishTime);
    headlines.push({
      title,
      publisher: typeof row.publisher === "string" ? row.publisher : "",
      link,
      published: Number.isFinite(seconds) && seconds > 0 ? new Date(seconds * 1000).toISOString() : "",
    });
    if (headlines.length === 5) break;
  }
  return headlines;
}

export function summarizeResearch(symbol: string, closes: number[], volumes: number[], headlines: Headline[]): ResearchBrief {
  const last = closes.length ? closes[closes.length - 1] : 0;
  const weekBase = closes.length > 5 ? closes[closes.length - 6] : undefined;
  const monthBase = closes.length > 1 ? closes[0] : undefined;
  const weekChange = last ? change(last, weekBase) : null;
  const dayChange = last ? change(last, closes.length > 1 ? closes[closes.length - 2] : undefined) : null;
  const monthChange = last ? change(last, monthBase) : null;
  const slope = weekChange ?? dayChange ?? 0;
  const direction = slope > 0.01 ? "rising" : slope < -0.01 ? "falling" : "flat";
  const earlier = volumes.slice(0, -1).filter((value) => value > 0);
  const latestVolume = volumes.length ? volumes[volumes.length - 1] : 0;
  const average = earlier.length ? earlier.reduce((sum, value) => sum + value, 0) / earlier.length : 0;
  const high = closes.length ? Math.max(...closes) : 0;
  const low = closes.length ? Math.min(...closes) : 0;
  return {
    symbol,
    direction,
    last: price(last),
    dayChange,
    weekChange,
    monthChange,
    high: price(high),
    low: price(low),
    volumeRatio: average > 0 && latestVolume > 0 ? latestVolume / average : null,
    headlines,
    trendNote: closes.length ? "" : "The price trend could not be loaded.",
    newsNote: headlines.length ? "" : "No headlines came back for this symbol.",
  };
}

async function readJson(fetchImpl: FetchLike, url: string, headers: Record<string, string> = {}): Promise<unknown> {
  const response = await fetchImpl(url, { headers: { Accept: "application/json", "User-Agent": "QuantShift", ...headers }, cache: "no-store" });
  if (!response.ok) throw new Error(String(response.status));
  return response.json();
}

export async function readActivity(symbol: string, fetchImpl: FetchLike = fetch): Promise<number[]> {
  const name = normalizeSymbol(symbol);
  if (!name) throw new Error("Enter a symbol such as NVDA or BTC-USD.");
  if (isCryptoPair(name)) {
    const body = await readJson(fetchImpl, `https://api.exchange.coinbase.com/products/${encodeURIComponent(name)}/candles?granularity=300`);
    return closesFromCoinbaseCandles(body).closes.slice(-80);
  }
  const body = await readJson(fetchImpl, `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(name)}?interval=5m&range=1d`);
  return closesFromYahooChart(body).closes.slice(-80);
}

export async function readResearch(symbol: string, fetchImpl: FetchLike = fetch): Promise<ResearchBrief> {
  const name = normalizeSymbol(symbol);
  if (!name) throw new Error("Enter a symbol such as NVDA or BTC-USD.");
  const newsUrl = `https://query2.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(name)}&newsCount=5&quotesCount=0`;
  const barsPromise = isCryptoPair(name)
    ? readJson(fetchImpl, `https://api.exchange.coinbase.com/products/${encodeURIComponent(name)}/candles?granularity=86400`).then(closesFromCoinbaseCandles)
    : readJson(fetchImpl, `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(name)}?interval=1d&range=1mo`).then(closesFromYahooChart);
  const [bars, headlines] = await Promise.all([
    barsPromise.catch(() => ({ closes: [] as number[], volumes: [] as number[] })),
    readJson(fetchImpl, newsUrl).then(parseHeadlines).catch(() => [] as Headline[]),
  ]);
  if (!bars.closes.length && !headlines.length) throw new Error("No research came back for that symbol.");
  return summarizeResearch(name, bars.closes.slice(-22), bars.volumes.slice(-22), headlines);
}
