"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { Sparkline } from "@/components/dashboard/Sparkline";
import { useAuth } from "@/lib/auth-context";
import { SYMBOL_LIBRARY } from "@/lib/symbol-library";
import type { ResearchBrief } from "@/lib/symbol-research";
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
  const [message, setMessage] = useState("");
  const [watching, setWatching] = useState("");
  const [quote, setQuote] = useState<LiveQuote | null>(null);
  const [session, setSession] = useState<number[]>([]);
  const [liveTicks, setLiveTicks] = useState<number[]>([]);
  const [research, setResearch] = useState<ResearchBrief | null>(null);
  const [researchNote, setResearchNote] = useState("");

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
    setSession([]);
    setLiveTicks([]);
    fetch(`/api/me/symbols/activity?symbol=${encodeURIComponent(watching)}`)
      .then((response) => response.json())
      .then((data) => setSession(Array.isArray(data.closes) ? data.closes : []))
      .catch(() => setSession([]));
    const source = new EventSource(`/api/me/symbols/stream?symbol=${encodeURIComponent(watching)}`);
    source.onmessage = (event) => {
      try {
        const next = JSON.parse(event.data) as LiveQuote;
        setQuote(next);
        const price = Number(next.price);
        if (Number.isFinite(price)) {
          setLiveTicks((ticks) => (ticks[ticks.length - 1] === price ? ticks : [...ticks, price].slice(-60)));
        }
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
    setResearch(null);
    setResearchNote("");
    setWatching(next);
  };

  const openResearch = async (name: string) => {
    const next = normalizeSymbol(name);
    if (!next) {
      setMessage("Enter a symbol such as NVDA or BTC-USD.");
      return;
    }
    setMessage("");
    if (watching !== next) watch(next);
    setResearch(null);
    setResearchNote("Pulling headlines and the trend.");
    const response = await fetch(`/api/me/symbols/research?symbol=${encodeURIComponent(next)}`);
    const data = await response.json();
    if (!response.ok) {
      setResearchNote(data.error || "The research could not be loaded.");
      return;
    }
    setResearch(data.research);
    setResearchNote("");
    await add(next, "research");
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
  const graph = [...session, ...liveTicks];
  const percent = (value: number | null) => {
    if (value == null) return "—";
    const sign = value > 0 ? "+" : "";
    return `${sign}${(value * 100).toFixed(1)}%`;
  };
  const direction = research?.direction === "rising" ? "Rising" : research?.direction === "falling" ? "Falling" : "Flat";

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        <ReleaseBanner userId={user.id} />
        <div className="p-8 space-y-6 max-w-3xl">
          <div>
            <h1 className="text-3xl font-bold text-white">Symbols</h1>
            <p className="text-slate-400 mt-2">
              Watch a name for the session graph and the live quote. Research pulls headlines and the recent trend so you can decide whether it belongs on a book. Neither action places an order. The house books keep their own symbol list.
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
                <div>
                  <p className="text-xs text-slate-500 mb-2">Session trend. The right edge moves with the live quote.</p>
                  {graph.length > 1 ? <Sparkline values={graph} width={640} height={120} /> : <p className="text-slate-500 text-sm">Waiting for the first prices.</p>}
                </div>
                <div className="flex gap-3">
                  <button onClick={() => add(watching, "trade")} className="px-4 py-2 rounded-lg bg-cyan-600 text-white">Add to book</button>
                  <button onClick={() => openResearch(watching)} className="px-4 py-2 rounded-lg border border-slate-600 text-white">Research</button>
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
            <button onClick={() => openResearch(symbol)} className="px-4 py-2 rounded-lg border border-slate-600 text-white">Research</button>
            <button onClick={() => add(symbol, "trade")} className="px-4 py-2 rounded-lg bg-cyan-600 text-white">Add to book</button>
          </div>
          {message && <p className="text-amber-300">{message}</p>}
          {(research || researchNote) && (
            <section className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 space-y-4">
              <div>
                <h2 className="text-xl font-semibold text-white">{research?.symbol || watching} research</h2>
                <p className="text-slate-400 text-sm mt-1">Headlines and the recent trend. This does not place an order.</p>
              </div>
              {researchNote && <p className="text-slate-300">{researchNote}</p>}
              {research && (
                <>
                  <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                    <div><p className="text-slate-500">Trend</p><p className="text-white">{direction}</p></div>
                    <div><p className="text-slate-500">Day</p><p className="text-white">{percent(research.dayChange)}</p></div>
                    <div><p className="text-slate-500">Week</p><p className="text-white">{percent(research.weekChange)}</p></div>
                    <div><p className="text-slate-500">Month</p><p className="text-white">{percent(research.monthChange)}</p></div>
                    <div><p className="text-slate-500">High</p><p className="text-white">{research.high || "—"}</p></div>
                    <div><p className="text-slate-500">Low</p><p className="text-white">{research.low || "—"}</p></div>
                    <div><p className="text-slate-500">Volume</p><p className="text-white">{research.volumeRatio == null ? "—" : `${research.volumeRatio.toFixed(1)}× recent`}</p></div>
                  </div>
                  {research.trendNote && <p className="text-amber-300 text-sm">{research.trendNote}</p>}
                  <div className="space-y-2">
                    {research.headlines.map((headline) => (
                      <a key={headline.link} href={headline.link} target="_blank" rel="noreferrer" className="block text-cyan-300 hover:text-cyan-200">
                        {headline.title}
                        {headline.publisher ? <span className="text-slate-500"> · {headline.publisher}</span> : null}
                      </a>
                    ))}
                    {research.newsNote && <p className="text-slate-400 text-sm">{research.newsNote}</p>}
                  </div>
                </>
              )}
            </section>
          )}
          <div className="space-y-2">
            {symbols.map((mark) => (
              <div key={mark.id} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex justify-between gap-4">
                <button onClick={() => watch(mark.symbol)} className="text-white hover:text-cyan-300">{mark.symbol}</button>
                <span className="flex gap-4 items-center">
                  {mark.intent === "research" ? (
                    <button onClick={() => openResearch(mark.symbol)} className="text-cyan-300 hover:text-cyan-200">Open research</button>
                  ) : (
                    <span className="text-slate-400">Trade</span>
                  )}
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
