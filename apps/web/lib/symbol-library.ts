/**Names a person can open from the Symbols page. The house books keep their own list. */

export type SymbolGroup = {
  id: "equity" | "crypto";
  label: string;
  symbols: string[];
};

export const SYMBOL_LIBRARY: SymbolGroup[] = [
  {
    id: "equity",
    label: "US stocks",
    symbols: [
      "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO",
      "JPM", "V", "UNH", "XOM", "JNJ", "WMT", "MA", "PG", "HD", "COST",
      "LLY", "NFLX", "AMD", "CRM", "ORCL", "BAC", "KO", "PEP", "DIS", "INTC",
    ],
  },
  {
    id: "crypto",
    label: "Crypto",
    symbols: [
      "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD",
      "AVAX-USD", "LINK-USD", "ADA-USD", "DOT-USD", "LTC-USD",
    ],
  },
];

export function librarySymbols(): string[] {
  return SYMBOL_LIBRARY.flatMap((group) => group.symbols);
}
