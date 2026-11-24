import assert from "node:assert/strict";
import { librarySymbols } from "../lib/symbol-library";
import { isCryptoPair, parseCoinbaseTicker, parseYahooChart, readQuote } from "../lib/symbol-quote";

const names = librarySymbols();
assert.equal(new Set(names).size, names.length);
assert.equal(names.includes("NVDA"), true);
assert.equal(names.includes("BTC-USD"), true);
assert.equal(isCryptoPair("BTC-USD"), true);
assert.equal(isCryptoPair("NVDA"), false);

const coinbase = parseCoinbaseTicker(
  { price: "59702.68", bid: "59702.67", ask: "59702.69", time: "2026-11-24T21:09:00.000Z" },
  "BTC-USD",
);
assert.equal(coinbase.price, "59702.68");
assert.equal(coinbase.source, "coinbase");
assert.throws(() => parseCoinbaseTicker({}, "BTC-USD"), /No quote/);

const yahoo = parseYahooChart(
  { chart: { result: [{ meta: { regularMarketPrice: 155.38, regularMarketTime: 1795554001 } }] } },
  "NVDA",
);
assert.equal(yahoo.price, "155.38");
assert.equal(yahoo.source, "yahoo");
assert.equal(yahoo.asOf, new Date(1795554001 * 1000).toISOString());

async function main() {
  const calls: string[] = [];
  const fetchImpl = (async (url: string | URL | Request) => {
    calls.push(String(url));
    return new Response(JSON.stringify({ price: "1.25", bid: "1.24", ask: "1.26", time: "2026-11-24T21:09:00.000Z" }), { status: 200 });
  }) as typeof fetch;
  const quote = await readQuote("eth-usd", fetchImpl);
  assert.equal(quote.symbol, "ETH-USD");
  assert.equal(calls[0].includes("ETH-USD"), true);
  assert.equal(await readQuote("nope!", fetchImpl).then(() => "", () => "rejected"), "rejected");
  assert.equal(calls.length, 1);
  console.log("symbol-quote-check passed");
}

main();
