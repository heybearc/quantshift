import { createHash, createHmac, createSign, randomBytes, randomUUID } from "crypto";
import { catalogBroker, type BrokerEnvironment } from "./broker-catalog";
import { redactSecrets } from "./credential-vault";

export type Holding = { symbol: string; quantity: string; value: string };

export type AccountSnapshot = {
  account: string;
  currency: string;
  cash: string;
  equity: string;
  buyingPower: string;
  holdings: Holding[];
};

export type BrokerCredentials = { apiKey: string; apiSecret: string };

export type OrderTicket = {
  symbol: string;
  side: "buy" | "sell";
  quantity: string;
  confirmLive: boolean;
};

export type PlacedOrder = {
  brokerOrderId: string;
  status: string;
  message: string;
};

type FetchLike = typeof fetch;

export class BrokerError extends Error {
  status: number;
  constructor(message: string, status = 400) {
    super(message);
    this.status = status;
  }
}

const QTY = /^(?:[1-9]\d{0,6}|0)(?:\.\d{1,8})?$/;

export function parseCredentials(value: unknown): BrokerCredentials {
  const body = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  const apiKey = typeof body.apiKey === "string" ? body.apiKey.trim() : "";
  const apiSecret = typeof body.apiSecret === "string" ? body.apiSecret.trim() : "";
  if (apiKey.length < 8 || apiKey.length > 400) {
    throw new BrokerError("Enter the API key from the broker.");
  }
  if (apiSecret.length < 8 || apiSecret.length > 8000) {
    throw new BrokerError("Enter the API secret from the broker.");
  }
  return { apiKey, apiSecret };
}

export function parseOrder(value: unknown, environment: BrokerEnvironment): OrderTicket {
  const body = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  const symbol = typeof body.symbol === "string" ? body.symbol.trim().toUpperCase() : "";
  const side = body.side === "sell" ? "sell" : body.side === "buy" ? "buy" : "";
  const quantity = typeof body.quantity === "string" ? body.quantity.trim() : String(body.quantity ?? "").trim();
  if (!/^[A-Z0-9][A-Z0-9.\-\/]{0,20}$/.test(symbol)) {
    throw new BrokerError("Enter a symbol the broker will accept.");
  }
  if (!side) throw new BrokerError("Choose buy or sell.");
  if (!QTY.test(quantity) || Number(quantity) <= 0) {
    throw new BrokerError("Enter a quantity greater than zero.");
  }
  if (environment === "live" && body.confirmLive !== true) {
    throw new BrokerError("Live orders need an explicit confirmation.");
  }
  return { symbol, side, quantity, confirmLive: body.confirmLive === true };
}

export function keyHint(apiKey: string): string {
  const tail = apiKey.slice(-4);
  return `••••${tail}`;
}

export function krakenSignature(path: string, nonce: string, postData: string, secret: string): string {
  const hash = createHash("sha256").update(nonce + postData).digest();
  const hmac = createHmac("sha512", Buffer.from(secret, "base64"));
  hmac.update(path);
  hmac.update(hash);
  return hmac.digest("base64");
}

export function coinbaseJwt(keyName: string, privateKey: string, method: string, requestPath: string): string {
  const header = { alg: "ES256", kid: keyName, nonce: randomBytes(16).toString("hex"), typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    sub: keyName,
    iss: "cdp",
    nbf: now,
    exp: now + 120,
    uri: `${method} api.coinbase.com${requestPath}`,
  };
  const encoded = (value: object) => Buffer.from(JSON.stringify(value)).toString("base64url");
  const signingInput = `${encoded(header)}.${encoded(payload)}`;
  const pem = privateKey.includes("BEGIN") ? privateKey.replace(/\\n/g, "\n") : privateKey;
  const signer = createSign("SHA256");
  signer.update(signingInput);
  signer.end();
  const signature = signer.sign({ key: pem, dsaEncoding: "ieee-p1363" });
  return `${signingInput}.${signature.toString("base64url")}`;
}

function alpacaBase(environment: BrokerEnvironment): string {
  return environment === "live" ? "https://api.alpaca.markets" : "https://paper-api.alpaca.markets";
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

function brokerMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const body = payload as Record<string, unknown>;
  const message = body.message || body.error || body.msg;
  if (typeof message === "string" && message.trim()) return message;
  if (Array.isArray(body.error) && body.error.length) return String(body.error[0]);
  return fallback;
}

async function brokerFetch(fetchImpl: FetchLike, url: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    return await fetchImpl(url, { ...init, signal: controller.signal });
  } catch (error) {
    const message = error instanceof Error && error.name === "AbortError" ? "The broker did not answer in time." : "The broker could not be reached.";
    throw new BrokerError(message, 502);
  } finally {
    clearTimeout(timer);
  }
}

export async function readAccount(
  venue: string,
  environment: BrokerEnvironment,
  credentials: BrokerCredentials,
  fetchImpl: FetchLike = fetch
): Promise<AccountSnapshot> {
  const broker = catalogBroker(venue);
  if (!broker || broker.adapter !== "ready") throw new BrokerError("That broker cannot accept a connection yet.");
  if (!broker.environments.includes(environment)) throw new BrokerError("Choose a supported account type for this broker.");
  if (venue === "alpaca") return readAlpaca(environment, credentials, fetchImpl);
  if (venue === "kraken") return readKraken(credentials, fetchImpl);
  if (venue === "coinbase") return readCoinbase(credentials, fetchImpl);
  throw new BrokerError("That broker cannot accept a connection yet.");
}

export async function sendOrder(
  venue: string,
  environment: BrokerEnvironment,
  credentials: BrokerCredentials,
  order: OrderTicket,
  fetchImpl: FetchLike = fetch
): Promise<PlacedOrder> {
  if (venue === "alpaca") return sendAlpaca(environment, credentials, order, fetchImpl);
  if (venue === "kraken") return sendKraken(credentials, order, fetchImpl);
  if (venue === "coinbase") return sendCoinbase(credentials, order, fetchImpl);
  throw new BrokerError("That broker cannot accept an order yet.");
}

async function readAlpaca(environment: BrokerEnvironment, credentials: BrokerCredentials, fetchImpl: FetchLike): Promise<AccountSnapshot> {
  const headers = {
    "APCA-API-KEY-ID": credentials.apiKey,
    "APCA-API-SECRET-KEY": credentials.apiSecret,
  };
  const base = alpacaBase(environment);
  const accountResponse = await brokerFetch(fetchImpl, `${base}/v2/account`, { headers });
  const account = await readBody(accountResponse);
  if (!accountResponse.ok) {
    throw new BrokerError(redactSecrets(brokerMessage(account, "Alpaca rejected the key."), [credentials.apiKey, credentials.apiSecret]), 400);
  }
  const row = account as Record<string, string>;
  const positionsResponse = await brokerFetch(fetchImpl, `${base}/v2/positions`, { headers });
  const positions = positionsResponse.ok ? await readBody(positionsResponse) : [];
  const holdings = Array.isArray(positions)
    ? positions.map((position) => {
        const item = position as Record<string, string>;
        return { symbol: item.symbol || "", quantity: String(item.qty || "0"), value: String(item.market_value || "") };
      })
    : [];
  return {
    account: row.account_number || "",
    currency: row.currency || "USD",
    cash: String(row.cash || "0"),
    equity: String(row.equity || "0"),
    buyingPower: String(row.buying_power || "0"),
    holdings,
  };
}

async function sendAlpaca(
  environment: BrokerEnvironment,
  credentials: BrokerCredentials,
  order: OrderTicket,
  fetchImpl: FetchLike
): Promise<PlacedOrder> {
  const response = await brokerFetch(fetchImpl, `${alpacaBase(environment)}/v2/orders`, {
    method: "POST",
    headers: {
      "APCA-API-KEY-ID": credentials.apiKey,
      "APCA-API-SECRET-KEY": credentials.apiSecret,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      symbol: order.symbol,
      qty: order.quantity,
      side: order.side,
      type: "market",
      time_in_force: "day",
    }),
  });
  const payload = await readBody(response);
  if (!response.ok) {
    throw new BrokerError(redactSecrets(brokerMessage(payload, "Alpaca rejected the order."), [credentials.apiKey, credentials.apiSecret]), 502);
  }
  const row = payload as Record<string, string>;
  return { brokerOrderId: row.id || "", status: row.status || "accepted", message: "Order accepted by Alpaca." };
}

async function krakenPrivate(path: string, fields: Record<string, string>, credentials: BrokerCredentials, fetchImpl: FetchLike) {
  const nonce = `${Date.now()}${Math.floor(Math.random() * 1000)}`;
  const postData = new URLSearchParams({ nonce, ...fields }).toString();
  const response = await brokerFetch(fetchImpl, `https://api.kraken.com${path}`, {
    method: "POST",
    headers: {
      "API-Key": credentials.apiKey,
      "API-Sign": krakenSignature(path, nonce, postData, credentials.apiSecret),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: postData,
  });
  const payload = (await readBody(response)) as { error?: string[]; result?: Record<string, unknown> };
  if (!response.ok || (payload.error && payload.error.length)) {
    throw new BrokerError(redactSecrets(payload.error?.[0] || "Kraken rejected the request.", [credentials.apiKey, credentials.apiSecret]), response.ok ? 400 : 502);
  }
  return payload.result || {};
}

async function readKraken(credentials: BrokerCredentials, fetchImpl: FetchLike): Promise<AccountSnapshot> {
  const balances = await krakenPrivate("/0/private/Balance", {}, credentials, fetchImpl);
  const holdings = Object.entries(balances)
    .filter(([, amount]) => Number(amount) > 0)
    .map(([symbol, amount]) => ({ symbol, quantity: String(amount), value: "" }));
  const cash = String(balances.ZUSD || balances.USD || "0");
  return {
    account: "Kraken spot",
    currency: "USD",
    cash,
    equity: cash,
    buyingPower: cash,
    holdings,
  };
}

async function sendKraken(credentials: BrokerCredentials, order: OrderTicket, fetchImpl: FetchLike): Promise<PlacedOrder> {
  const pair = order.symbol.replace("/", "");
  const result = await krakenPrivate(
    "/0/private/AddOrder",
    { pair, type: order.side, ordertype: "market", volume: order.quantity },
    credentials,
    fetchImpl
  );
  const txid = Array.isArray(result.txid) ? String(result.txid[0] || "") : "";
  return { brokerOrderId: txid, status: "accepted", message: "Order accepted by Kraken." };
}

async function coinbase(method: string, requestPath: string, credentials: BrokerCredentials, fetchImpl: FetchLike, body?: string) {
  const token = coinbaseJwt(credentials.apiKey, credentials.apiSecret, method, requestPath);
  const response = await brokerFetch(fetchImpl, `https://api.coinbase.com${requestPath}`, {
    method,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body,
  });
  const payload = await readBody(response);
  if (!response.ok) {
    throw new BrokerError(redactSecrets(brokerMessage(payload, "Coinbase rejected the request."), [credentials.apiKey, credentials.apiSecret]), response.status === 401 ? 400 : 502);
  }
  return payload;
}

async function readCoinbase(credentials: BrokerCredentials, fetchImpl: FetchLike): Promise<AccountSnapshot> {
  const payload = (await coinbase("GET", "/api/v3/brokerage/accounts?limit=250", credentials, fetchImpl)) as {
    accounts?: { currency?: string; available_balance?: { value?: string } }[];
  };
  const accounts = payload.accounts || [];
  const cashAccounts = accounts.filter((account) => ["USD", "USDC", "USDT"].includes(account.currency || ""));
  const cash = cashAccounts.reduce((sum, account) => sum + Number(account.available_balance?.value || 0), 0);
  const holdings = accounts
    .filter((account) => !["USD", "USDC", "USDT"].includes(account.currency || "") && Number(account.available_balance?.value || 0) > 0)
    .map((account) => ({
      symbol: account.currency || "",
      quantity: String(account.available_balance?.value || "0"),
      value: "",
    }));
  return {
    account: "Coinbase Advanced Trade",
    currency: "USD",
    cash: cash.toFixed(2),
    equity: cash.toFixed(2),
    buyingPower: cash.toFixed(2),
    holdings,
  };
}

async function sendCoinbase(credentials: BrokerCredentials, order: OrderTicket, fetchImpl: FetchLike): Promise<PlacedOrder> {
  const product = order.symbol.includes("-") ? order.symbol : order.symbol;
  const payload = (await coinbase(
    "POST",
    "/api/v3/brokerage/orders",
    credentials,
    fetchImpl,
    JSON.stringify({
      client_order_id: randomUUID(),
      product_id: product,
      side: order.side.toUpperCase(),
      order_configuration: { market_market_ioc: { base_size: order.quantity } },
    })
  )) as { success?: boolean; success_response?: { order_id?: string }; error_response?: { message?: string } };
  if (payload.success === false) {
    throw new BrokerError(redactSecrets(payload.error_response?.message || "Coinbase rejected the order.", [credentials.apiKey, credentials.apiSecret]), 502);
  }
  return {
    brokerOrderId: payload.success_response?.order_id || "",
    status: "accepted",
    message: "Order accepted by Coinbase.",
  };
}
