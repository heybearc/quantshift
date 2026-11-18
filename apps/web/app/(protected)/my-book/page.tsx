"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";

interface Bot {
  venue: string;
  status: string;
  tradingMode: string;
}

export default function MyBookPage() {
  const { user } = useAuth();
  const [mode, setMode] = useState("house");
  const [bots, setBots] = useState<Bot[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!user) return;
    fetch("/api/me/book")
      .then((response) => response.json())
      .then((data) => {
        setMode(data.mode || "house");
        setBots(data.bots || []);
      })
      .catch(() => setMessage("The desk could not be loaded."));
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

  if (!user) return null;

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        <ReleaseBanner userId={user.id} />
        <div className="p-8 space-y-6 max-w-3xl">
          <div>
            <h1 className="text-3xl font-bold text-white">My book</h1>
            <p className="text-slate-400 mt-2">
              House mode follows the shared paper books. Personal mode records a stopped paper bot for Alpaca, Coinbase, and Kraken. Those bots do not trade yet.
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => choose("house")} className={`px-4 py-2 rounded-lg ${mode === "house" ? "bg-cyan-600 text-white" : "bg-slate-800 text-slate-300"}`}>House books</button>
            <button onClick={() => choose("personal")} className={`px-4 py-2 rounded-lg ${mode === "personal" ? "bg-cyan-600 text-white" : "bg-slate-800 text-slate-300"}`}>My brokers</button>
          </div>
          {mode === "personal" && (
            <div className="space-y-3">
              {bots.map((bot) => (
                <div key={bot.venue} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex justify-between">
                  <span className="text-white capitalize">{bot.venue}</span>
                  <span className="text-slate-400">{bot.status} · {bot.tradingMode}</span>
                </div>
              ))}
            </div>
          )}
          {message && <p className="text-amber-300">{message}</p>}
        </div>
      </main>
    </div>
  );
}
