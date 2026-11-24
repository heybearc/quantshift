"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { SYMBOL_LIBRARY } from "@/lib/symbol-library";
import { normalizeSymbol } from "@/lib/user-desk";

interface Mark {
  id: string;
  symbol: string;
  intent: string;
}

interface LiveQuote {
  symbol: string;
  price?: string;
  bid?: string;
  ask?: string;
  asOf?: string;
  source?: string;
  error?: string;
}

export default function SymbolsPage() {
  const { user } = useAuth();
  const [symbols, setSymbols] = useState<Mark[]>([]);
  const [symbol, setSymbol] = useState("");
  const [intent, setIntent] = useState("trade");
  const [message, setMessage] = useState("");
  const [watching, setWatching] = useState("");
  const [quote, setQuote] = useState<LiveQuote | null>(null);

  const load = () => {
    fetch("/api/me/symbols")
      .then((response) => response.json())
      .then((data) => setSymbols(data.symbols || []))
      .catch(() => setMessage("The symbol list could not be loaded."));
  };

  useEffect(() => {
    if (user) load();
  }, [user]);

  useEffect(() => {
    if (!watching) return;
    const source = new EventSource(`/api/me/symbols/stream?symbol=${encodeURIComponent(watching)}`);
    source.onmessage = (event) => {
      try {
        setQuote(JSON.parse(event.data) as LiveQuote);
      } catch {
        setQuote({ symbol: watching, error: "The quote paused." });
      }
    };
    source.onerror = () => {
      setQuote((current) => current || { symbol: watching, error: "The live quote paused. It will retry." });
    };
    return () => source.close();
  }, [watching]);

  const watch = (name: string) => {
    const next = normalizeSymbol(name);
    if (!next) {
      setMessage("Enter a symbol such as NVDA or BTC-USD.");
      return;
    }
    setMessage("");
    setQuote(null);
    setWatching(next);
  };

  const add = async (name: string, markIntent: string) => {
    setMessage("");
    const response = await fetch("/api/me/symbols", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: name, intent: markIntent }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "That symbol was not saved.");
      return;
    }
    setSymbol("");
    load();
  };

  const remove = async (name: string) => {
    await fetch(`/api/me/symbols?symbol=${encodeURIComponent(name)}`, { method: "DELETE" });
    load();
  };

  if (!user) return null;

  const savedNames = symbols.map((mark) => mark.symbol);
  const clock = quote?.asOf ? new Date(quote.asOf).toLocaleTimeString() : "";

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        <ReleaseBanner userId={user.id} />
        <div className="p-8 space-y-6 max-w-3xl">
          <div>
            <h1 className="text-3xl font-bold text-white">Symbols</h1>
            <p className="text-slate-400 mt-2">
              Open a name to watch the live quote. A trade mark is the list a personal book will scan. A research mark is for looking. The house books keep their own symbol list.
            </p>
          </div>

          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 space-y-4">
            <label className="block text-sm text-slate-400" htmlFor="symbol-library">Library</label>
            <select
              id="symbol-library"
              value={watching}
              onChange={(event) => watch(event.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
            >
              <option value="">Choose a symbol</option>
              {savedNames.length > 0 && (
                <optgroup label="Your book">
                  {savedNames.map((name) => (
                    <option key={`book-${name}`} value={name}>{name}</option>
                  ))}
                </optgroup>
              )}
              {SYMBOL_LIBRARY.map((group) => (
                <optgroup key={group.id} label={group.label}>
                  {group.symbols.map((name) => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </optgroup>
              ))}
            </select>

            {watching && (
              <div className="space-y-3">
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <p className="text-slate-400 text-sm">{watching}</p>
                    <p className="text-3xl font-bold text-white">{quote?.price || "…"}</p>
                  </div>
                  <p className="text-slate-400 text-sm text-right">
                    {quote?.error ? quote.error : clock ? `Updated ${clock}` : "Connecting"}
                  </p>
                </div>
                <div className="flex gap-6 text-sm text-slate-300">
                  <span>Bid {quote?.bid || "—"}</span>
                  <span>Ask {quote?.ask || "—"}</span>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => add(watching, "trade")} className="px-4 py-2 rounded-lg bg-cyan-600 text-white">Add to book</button>
                  <button onClick={() => add(watching, "research")} className="px-4 py-2 rounded-lg border border-slate-600 text-white">Research only</button>
                </div>
                <p className="text-xs text-slate-500">Watching a quote does not place an order.</p>
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <input
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              placeholder="NVDA or BTC-USD"
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
            <button onClick={() => watch(symbol)} className="px-4 py-2 rounded-lg border border-slate-600 text-white">Watch</button>
            <select value={intent} onChange={(event) => setIntent(event.target.value)} className="bg-slate-800 border border-slate-700 rounded-lg px-3 text-white">
              <option value="trade">Trade</option>
              <option value="research">Research</option>
            </select>
            <button onClick={() => add(symbol, intent)} className="px-4 py-2 rounded-lg bg-cyan-600 text-white">Save</button>
          </div>
          {message && <p className="text-amber-300">{message}</p>}
          <div className="space-y-2">
            {symbols.map((mark) => (
              <div key={mark.id} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex justify-between">
                <button onClick={() => watch(mark.symbol)} className="text-white hover:text-cyan-300">{mark.symbol}</button>
                <span className="flex gap-4 items-center">
                  <span className="text-slate-400">{mark.intent}</span>
                  <button onClick={() => remove(mark.symbol)} className="text-slate-400 hover:text-white">Remove</button>
                </span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
