import assert from "node:assert/strict";
import { createVerify, generateKeyPairSync } from "node:crypto";
import { coinbaseJwt, krakenSignature, parseOrder, readAccount } from "../lib/broker-gateway";
import { openCredentials, redactSecrets, sealCredentials } from "../lib/credential-vault";

async function main() {
  const env = { BROKER_VAULT_KEY: "test-vault-key-value" };
  const sealed = sealCredentials({ apiKey: "key-12345678", apiSecret: "secret-value" }, env);
  const opened = openCredentials(sealed, env);
  assert.equal(opened.apiKey, "key-12345678");
  assert.equal(redactSecrets("rejected key-12345678", ["key-12345678"]), "rejected ••••");

  assert.throws(() => parseOrder({ symbol: "AAPL", side: "buy", quantity: "1" }, "live"), /confirmation/);
  const paper = parseOrder({ symbol: "aapl", side: "buy", quantity: "1" }, "paper");
  assert.equal(paper.symbol, "AAPL");
  assert.throws(() => parseOrder({ symbol: "AAPL", side: "buy", quantity: "0" }, "paper"), /quantity/);

  const secret = Buffer.from("kraken-secret").toString("base64");
  const signature = krakenSignature("/0/private/Balance", "1", "nonce=1", secret);
  assert.equal(signature, krakenSignature("/0/private/Balance", "1", "nonce=1", secret));

  const { privateKey, publicKey } = generateKeyPairSync("ec", { namedCurve: "P-256" });
  const pem = privateKey.export({ type: "pkcs8", format: "pem" }).toString();
  const token = coinbaseJwt("organizations/demo/apiKeys/key", pem, "GET", "/api/v3/brokerage/accounts");
  const [header, payload, signed] = token.split(".");
  const verifier = createVerify("SHA256");
  verifier.update(`${header}.${payload}`);
  verifier.end();
  assert.equal(verifier.verify({ key: publicKey, dsaEncoding: "ieee-p1363" }, Buffer.from(signed, "base64url")), true);

  const calls: string[] = [];
  const fetchImpl = (async (url: string | URL | Request) => {
    calls.push(String(url));
    if (String(url).endsWith("/v2/account")) {
      return new Response(JSON.stringify({ account_number: "PA123", currency: "USD", cash: "10", equity: "12", buying_power: "40" }), { status: 200 });
    }
    return new Response(JSON.stringify([{ symbol: "AAPL", qty: "1", market_value: "100" }]), { status: 200 });
  }) as typeof fetch;

  const snapshot = await readAccount("alpaca", "paper", { apiKey: "key-12345678", apiSecret: "secret-value-1" }, fetchImpl);
  assert.equal(snapshot.cash, "10");
  assert.equal(snapshot.holdings[0].symbol, "AAPL");
  assert.equal(calls[0].includes("paper-api.alpaca.markets"), true);
  console.log("broker gateway checks passed");
}

main();
