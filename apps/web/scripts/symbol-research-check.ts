import assert from "node:assert/strict";
import { closesFromCoinbaseCandles, closesFromYahooChart, parseHeadlines, summarizeResearch } from "../lib/symbol-research";

const yahoo = closesFromYahooChart({
  chart: { result: [{ indicators: { quote: [{ close: [100, null, 110], volume: [10, 1, 20] }] } }] },
});
assert.deepEqual(yahoo.closes, [100, 110]);
assert.deepEqual(yahoo.volumes, [10, 20]);

const candles = closesFromCoinbaseCandles([[20, 1, 2, 1, 1.5, 4], [10, 1, 2, 1, 1.2, 3]]);
assert.deepEqual(candles.closes, [1.2, 1.5]);

const headlines = parseHeadlines({
  news: [
    { title: "Chip demand holds", publisher: "Desk", link: "https://news.example/chip", providerPublishTime: 1795554001 },
    { title: "Skip", link: "http://news.example/plain" },
  ],
});
assert.equal(headlines.length, 1);
assert.equal(headlines[0].title, "Chip demand holds");

const rising = summarizeResearch("NVDA", [100, 101, 102, 103, 104, 110], [10, 10, 10, 10, 10, 20], headlines);
assert.equal(rising.direction, "rising");
assert.equal(rising.weekChange, 0.1);
assert.equal(rising.volumeRatio, 2);
assert.equal(rising.newsNote, "");

const quiet = summarizeResearch("XYZ", [], [], []);
assert.equal(quiet.direction, "flat");
assert.equal(quiet.trendNote.includes("could not"), true);
assert.equal(quiet.newsNote.includes("No headlines"), true);

console.log("symbol-research-check passed");
