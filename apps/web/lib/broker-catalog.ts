export type BrokerEnvironment = "paper" | "live";

export type BrokerCatalogEntry = {
  id: string;
  name: string;
  adapter: "ready" | "needed";
  markets: string;
  environments: BrokerEnvironment[];
  summary: string;
  fields: { id: "apiKey" | "apiSecret"; label: string; secret: boolean }[];
};

export const BROKER_CATALOG: BrokerCatalogEntry[] = [
  {
    id: "alpaca",
    name: "Alpaca",
    adapter: "ready",
    markets: "US stocks",
    environments: ["paper", "live"],
    summary: "Paper and live accounts. The key is checked against the account before it is stored.",
    fields: [
      { id: "apiKey", label: "API key ID", secret: false },
      { id: "apiSecret", label: "API secret key", secret: true },
    ],
  },
  {
    id: "coinbase",
    name: "Coinbase",
    adapter: "ready",
    markets: "Crypto",
    environments: ["live"],
    summary: "Coinbase Advanced Trade. Use the CDP API key name and the EC private key. This account is live.",
    fields: [
      { id: "apiKey", label: "API key name", secret: false },
      { id: "apiSecret", label: "API private key", secret: true },
    ],
  },
  {
    id: "kraken",
    name: "Kraken",
    adapter: "ready",
    markets: "Crypto",
    environments: ["live"],
    summary: "Kraken spot. Use an API key with funds and trading permission. Orders use the Kraken pair, such as XBTUSD.",
    fields: [
      { id: "apiKey", label: "API key", secret: false },
      { id: "apiSecret", label: "Private key", secret: true },
    ],
  },
  {
    id: "schwab",
    name: "Charles Schwab",
    adapter: "needed",
    markets: "US stocks",
    environments: [],
    summary: "Listed. An adapter is not built yet, so keys cannot be stored.",
    fields: [],
  },
  {
    id: "ibkr",
    name: "Interactive Brokers",
    adapter: "needed",
    markets: "Multi-asset",
    environments: [],
    summary: "Listed. An adapter is not built yet, so keys cannot be stored.",
    fields: [],
  },
  {
    id: "tradier",
    name: "Tradier",
    adapter: "needed",
    markets: "US stocks and options",
    environments: [],
    summary: "Listed. An adapter is not built yet, so keys cannot be stored.",
    fields: [],
  },
];

const BY_ID = new Map(BROKER_CATALOG.map((broker) => [broker.id, broker]));

export function catalogBroker(id: string): BrokerCatalogEntry | undefined {
  return BY_ID.get(id);
}

export function publicCatalog() {
  return BROKER_CATALOG.map((broker) => ({
    id: broker.id,
    name: broker.name,
    adapter: broker.adapter,
    markets: broker.markets,
    environments: broker.environments,
    summary: broker.summary,
    fields: broker.fields,
  }));
}
