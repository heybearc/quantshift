"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";

interface Bot {
  venue: string;
  displayName?: string;
  status: string;
  tradingMode: string;
  adapter?: string;
}

interface CatalogBroker {
  id: string;
  name: string;
  adapter: string;
  markets: string;
  environments: string[];
  summary: string;
  fields: { id: string; label: string; secret: boolean }[];
}

interface Holding {
  symbol: string;
  quantity: string;
  value: string;
}

interface Snapshot {
  account?: string;
  currency?: string;
  cash?: string;
  equity?: string;
  buyingPower?: string;
  holdings?: Holding[];
}

interface Connection {
  id: string;
  venue: string;
  environment: string;
  label: string;
  status: string;
  keyHint: string;
  lastError?: string | null;
  snapshot?: Snapshot | null;
}

interface BrokerRequestRow {
  id: string;
  name: string;
  website: string;
  docsUrl: string;
  notes: string;
  status: string;
  createdAt: string;
  user?: { email: string };
}

export default function MyBookPage() {
  const { user } = useAuth();
  const [mode, setMode] = useState("house");
  const [bots, setBots] = useState<Bot[]>([]);
  const [catalog, setCatalog] = useState<CatalogBroker[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [requests, setRequests] = useState<BrokerRequestRow[]>([]);
  const [queue, setQueue] = useState<BrokerRequestRow[]>([]);
  const [openVenue, setOpenVenue] = useState("");
  const [environment, setEnvironment] = useState("paper");
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [requestName, setRequestName] = useState("");
  const [website, setWebsite] = useState("");
  const [docsUrl, setDocsUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [side, setSide] = useState("buy");
  const [confirmLive, setConfirmLive] = useState(false);
  const [message, setMessage] = useState("");

  const loadDesk = async () => {
    const [book, linked, submitted] = await Promise.all([
      fetch("/api/me/book").then((response) => response.json()),
      fetch("/api/me/brokers/connections").then((response) => response.json()),
      fetch("/api/me/brokers/requests").then((response) => response.json()),
    ]);
    setMode(book.mode || "house");
    setBots(book.bots || []);
    setCatalog(linked.catalog || book.brokers || []);
    setConnections(linked.connections || []);
    setRequests(submitted.requests || []);
    if (user && (user.role === "ADMIN" || user.role === "SUPER_ADMIN")) {
      const review = await fetch("/api/me/brokers/requests?scope=queue").then((response) => response.json());
      setQueue(review.requests || []);
    }
  };

  useEffect(() => {
    if (!user) return;
    loadDesk().catch(() => setMessage("The desk could not be loaded."));
  }, [user]);

  const choose = async (next: string) => {
    setMessage("");
    const response = await fetch("/api/me/book", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: next }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "The desk could not be saved.");
      return;
    }
    setMode(data.mode);
    setBots(data.bots || []);
  };

  const connect = async (venue: string) => {
    setMessage("");
    const response = await fetch("/api/me/brokers/connections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ venue, environment, credentials: { apiKey, apiSecret } }),
    });
    const data = await response.json();
    setApiKey("");
    setApiSecret("");
    if (!response.ok) {
      setMessage(data.error || "The broker did not accept the key.");
      return;
    }
    setOpenVenue("");
    setMode("personal");
    setMessage(`${data.connection.label} is connected. The key is stored encrypted and is not shown again.`);
    await loadDesk();
  };

  const refresh = async (id: string) => {
    setMessage("");
    const response = await fetch(`/api/me/brokers/connections/${id}/account`);
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "The balance could not be read.");
      await loadDesk();
      return;
    }
    setConnections((current) => current.map((item) => (item.id === id ? data.connection : item)));
  };

  const disconnect = async (id: string) => {
    setMessage("");
    const response = await fetch(`/api/me/brokers/connections/${id}`, { method: "DELETE" });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "The connection could not be removed.");
      return;
    }
    await loadDesk();
  };

  const sendOrder = async (connection: Connection) => {
    setMessage("");
    const response = await fetch(`/api/me/brokers/connections/${connection.id}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol,
        side,
        quantity,
        confirmLive: connection.environment === "live" ? confirmLive : false,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "The order was not accepted.");
      return;
    }
    setSymbol("");
    setQuantity("");
    setConfirmLive(false);
    setMessage(`${data.order.side} ${data.order.quantity} ${data.order.symbol} accepted${data.order.brokerOrderId ? ` (${data.order.brokerOrderId})` : ""}.`);
  };

  const submitRequest = async (preset?: string) => {
    setMessage("");
    const response = await fetch("/api/me/brokers/requests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: preset || requestName,
        website,
        docsUrl,
        notes: preset ? "Please build the listed adapter." : notes,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "The broker could not be submitted.");
      return;
    }
    setRequestName("");
    setWebsite("");
    setDocsUrl("");
    setNotes("");
    setMessage(`${data.request.name} was submitted for review.`);
    await loadDesk();
  };

  if (!user) return null;
  const ready = catalog.filter((broker) => broker.adapter === "ready");
  const waiting = catalog.filter((broker) => broker.adapter !== "ready");

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        <ReleaseBanner userId={user.id} />
        <div className="p-8 space-y-8 max-w-4xl">
          <div>
            <h1 className="text-3xl font-bold text-white">My book</h1>
            <p className="text-slate-400 mt-2">
              House mode follows the shared paper books. My brokers is your own desk: connect an approved broker, keep the key encrypted, read the balance, and send a market order on that account.
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => choose("house")} className={`px-4 py-2 rounded-lg ${mode === "house" ? "bg-cyan-600 text-white" : "bg-slate-800 text-slate-300"}`}>House books</button>
            <button onClick={() => choose("personal")} className={`px-4 py-2 rounded-lg ${mode === "personal" ? "bg-cyan-600 text-white" : "bg-slate-800 text-slate-300"}`}>My brokers</button>
          </div>

          {mode === "personal" && (
            <div className="space-y-8">
              <section className="space-y-3">
                <h2 className="text-xl font-semibold text-white">Approved connections</h2>
                {ready.map((broker) => {
                  const linked = connections.filter((item) => item.venue === broker.id);
                  return (
                    <article key={broker.id} className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 space-y-4">
                      <div className="flex justify-between gap-4">
                        <div>
                          <h3 className="text-white font-medium">{broker.name}</h3>
                          <p className="text-slate-400 text-sm mt-1">{broker.markets}. {broker.summary}</p>
                        </div>
                        <button
                          onClick={() => {
                            setOpenVenue(openVenue === broker.id ? "" : broker.id);
                            setEnvironment(broker.environments[0] || "live");
                            setApiKey("");
                            setApiSecret("");
                          }}
                          className="px-4 py-2 rounded-lg bg-cyan-700 text-white h-fit"
                        >
                          Connect
                        </button>
                      </div>
                      {openVenue === broker.id && (
                        <form
                          className="grid gap-3 md:grid-cols-2"
                          onSubmit={(event) => {
                            event.preventDefault();
                            connect(broker.id);
                          }}
                        >
                          <label className="text-sm text-slate-300">
                            Account
                            <select value={environment} onChange={(event) => setEnvironment(event.target.value)} className="mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white">
                              {broker.environments.map((item) => (
                                <option key={item} value={item}>{item}</option>
                              ))}
                            </select>
                          </label>
                          <div />
                          <label className="text-sm text-slate-300">
                            {broker.fields[0]?.label || "API key"}
                            <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} autoComplete="off" className="mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white" />
                          </label>
                          <label className="text-sm text-slate-300">
                            {broker.fields[1]?.label || "API secret"}
                            <input value={apiSecret} onChange={(event) => setApiSecret(event.target.value)} type="password" autoComplete="off" className="mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white" />
                          </label>
                          <button type="submit" className="md:col-span-2 px-4 py-2 rounded-lg bg-cyan-600 text-white w-fit">Check the key and save</button>
                        </form>
                      )}
                      {linked.map((connection) => (
                        <div key={connection.id} className="border border-slate-700 rounded-lg p-4 space-y-3">
                          <div className="flex justify-between gap-3">
                            <div>
                              <p className="text-white">{connection.label} · {connection.environment}</p>
                              <p className="text-slate-400 text-sm">{connection.status} · key {connection.keyHint}</p>
                              {connection.lastError && <p className="text-amber-300 text-sm">{connection.lastError}</p>}
                            </div>
                            <div className="flex gap-2">
                              <button onClick={() => refresh(connection.id)} className="px-3 py-2 rounded-lg bg-slate-700 text-white">Refresh balance</button>
                              <button onClick={() => disconnect(connection.id)} className="px-3 py-2 rounded-lg bg-slate-900 text-slate-300">Remove</button>
                            </div>
                          </div>
                          {connection.snapshot && (
                            <div className="text-sm text-slate-300 grid grid-cols-2 md:grid-cols-4 gap-2">
                              <span>Cash {connection.snapshot.cash} {connection.snapshot.currency}</span>
                              <span>Equity {connection.snapshot.equity}</span>
                              <span>Buying power {connection.snapshot.buyingPower}</span>
                              <span>{connection.snapshot.account}</span>
                            </div>
                          )}
                          {connection.snapshot?.holdings && connection.snapshot.holdings.length > 0 && (
                            <ul className="text-sm text-slate-400">
                              {connection.snapshot.holdings.slice(0, 8).map((holding) => (
                                <li key={holding.symbol}>{holding.symbol} {holding.quantity}{holding.value ? ` · ${holding.value}` : ""}</li>
                              ))}
                            </ul>
                          )}
                          <form
                            className="flex flex-wrap gap-2 items-center"
                            onSubmit={(event) => {
                              event.preventDefault();
                              sendOrder(connection);
                            }}
                          >
                            <input value={symbol} onChange={(event) => setSymbol(event.target.value)} placeholder="Symbol" className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white w-32" />
                            <select value={side} onChange={(event) => setSide(event.target.value)} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white">
                              <option value="buy">Buy</option>
                              <option value="sell">Sell</option>
                            </select>
                            <input value={quantity} onChange={(event) => setQuantity(event.target.value)} placeholder="Quantity" className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white w-28" />
                            {connection.environment === "live" && (
                              <label className="text-sm text-amber-200 flex items-center gap-2">
                                <input type="checkbox" checked={confirmLive} onChange={(event) => setConfirmLive(event.target.checked)} />
                                Send this live order
                              </label>
                            )}
                            <button type="submit" className="px-4 py-2 rounded-lg bg-cyan-700 text-white">Send market order</button>
                          </form>
                        </div>
                      ))}
                    </article>
                  );
                })}
              </section>

              <section className="space-y-3">
                <h2 className="text-xl font-semibold text-white">Listed, adapter not built</h2>
                {waiting.map((broker) => (
                  <div key={broker.id} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex justify-between gap-4">
                    <div>
                      <p className="text-white">{broker.name}</p>
                      <p className="text-slate-400 text-sm">{broker.summary}</p>
                    </div>
                    <button onClick={() => submitRequest(broker.name)} className="px-4 py-2 rounded-lg bg-slate-700 text-white h-fit">Request adapter</button>
                  </div>
                ))}
                {bots.filter((bot) => bot.adapter === "needed").map((bot) => (
                  <p key={bot.venue} className="text-slate-500 text-sm">{bot.displayName || bot.venue} remains a paper slot until an adapter exists.</p>
                ))}
              </section>

              <section className="space-y-3">
                <h2 className="text-xl font-semibold text-white">Submit a broker we do not list</h2>
                <p className="text-slate-400 text-sm">This records a request for review. It does not store a key or send an order.</p>
                <form
                  className="grid gap-3"
                  onSubmit={(event) => {
                    event.preventDefault();
                    submitRequest();
                  }}
                >
                  <input value={requestName} onChange={(event) => setRequestName(event.target.value)} placeholder="Broker name" className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
                  <input value={website} onChange={(event) => setWebsite(event.target.value)} placeholder="Website" className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
                  <input value={docsUrl} onChange={(event) => setDocsUrl(event.target.value)} placeholder="API documentation address" className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
                  <textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="What you need to trade there" className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white min-h-24" />
                  <button type="submit" className="px-4 py-2 rounded-lg bg-slate-700 text-white w-fit">Submit for review</button>
                </form>
                {requests.length > 0 && (
                  <ul className="text-sm text-slate-300 space-y-1">
                    {requests.map((item) => (
                      <li key={item.id}>{item.name} · {item.status}</li>
                    ))}
                  </ul>
                )}
              </section>

              {queue.length > 0 && (
                <section className="space-y-2">
                  <h2 className="text-xl font-semibold text-white">Review queue</h2>
                  {queue.map((item) => (
                    <p key={item.id} className="text-sm text-slate-300">{item.name} · {item.user?.email || "member"} · {item.website || "no site"}</p>
                  ))}
                </section>
              )}
            </div>
          )}
          {message && <p className="text-amber-200">{message}</p>}
        </div>
      </main>
    </div>
  );
}
