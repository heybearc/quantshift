"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";

interface Mark {
  id: string;
  symbol: string;
  intent: string;
}

export default function SymbolsPage() {
  const { user } = useAuth();
  const [symbols, setSymbols] = useState<Mark[]>([]);
  const [symbol, setSymbol] = useState("");
  const [intent, setIntent] = useState("trade");
  const [message, setMessage] = useState("");

  const load = () => {
    fetch("/api/me/symbols")
      .then((response) => response.json())
      .then((data) => setSymbols(data.symbols || []))
      .catch(() => setMessage("The symbol list could not be loaded."));
  };

  useEffect(() => {
    if (user) load();
  }, [user]);

  const add = async () => {
    setMessage("");
    const response = await fetch("/api/me/symbols", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol, intent }),
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

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        <ReleaseBanner userId={user.id} />
        <div className="p-8 space-y-6 max-w-3xl">
          <div>
            <h1 className="text-3xl font-bold text-white">Symbols</h1>
            <p className="text-slate-400 mt-2">
              A trade mark is the list a personal book will scan. A research mark is for looking. The house books keep their own symbol list.
            </p>
          </div>
          <div className="flex gap-3">
            <input value={symbol} onChange={(event) => setSymbol(event.target.value)} placeholder="NVDA or BTC-USD" className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
            <select value={intent} onChange={(event) => setIntent(event.target.value)} className="bg-slate-800 border border-slate-700 rounded-lg px-3 text-white">
              <option value="trade">Trade</option>
              <option value="research">Research</option>
            </select>
            <button onClick={add} className="px-4 py-2 rounded-lg bg-cyan-600 text-white">Save</button>
          </div>
          {message && <p className="text-amber-300">{message}</p>}
          <div className="space-y-2">
            {symbols.map((mark) => (
              <div key={mark.id} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex justify-between">
                <span className="text-white">{mark.symbol}</span>
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
