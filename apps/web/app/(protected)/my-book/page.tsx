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

interface Broker {
  id: string;
  name: string;
  adapter: string;
}

export default function MyBookPage() {
  const { user } = useAuth();
  const [mode, setMode] = useState("house");
  const [bots, setBots] = useState<Bot[]>([]);
  const [brokers, setBrokers] = useState<Broker[]>([]);
  const [listed, setListed] = useState("");
  const [custom, setCustom] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!user) return;
    fetch("/api/me/book")
      .then((response) => response.json())
      .then((data) => {
        setMode(data.mode || "house");
        setBots(data.bots || []);
        setBrokers(data.brokers || []);
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

  const addBroker = async (name: string) => {
    setMessage("");
    const response = await fetch("/api/me/brokers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "The broker was not added.");
      return;
    }
    setMode("personal");
    setListed("");
    setCustom("");
    const refreshed = await fetch("/api/me/book").then((item) => item.json());
    setBots(refreshed.bots || []);
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
              House mode follows the shared paper books. Personal mode is your own set. Every broker stays available as paper. A broker we already trade gets a stopped paper bot. A broker we have not built yet gets a paper slot until its adapter exists.
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
                  <span className="text-white">{bot.displayName || bot.venue}</span>
                  <span className="text-slate-400">{bot.status} · paper{bot.adapter === "needed" ? " · adapter needed" : ""}</span>
                </div>
              ))}
              <div className="flex gap-3 pt-2">
                <select value={listed} onChange={(event) => setListed(event.target.value)} className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 text-white">
                  <option value="">Add a broker</option>
                  {brokers.map((broker) => (
                    <option key={broker.id} value={broker.id}>{broker.name}{broker.adapter === "needed" ? " (adapter needed)" : ""}</option>
                  ))}
                </select>
                <button onClick={() => addBroker(listed)} className="px-4 py-2 rounded-lg bg-slate-700 text-white">Add</button>
              </div>
              <div className="flex gap-3">
                <input value={custom} onChange={(event) => setCustom(event.target.value)} placeholder="A broker we do not list" className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white" />
                <button onClick={() => addBroker(custom)} className="px-4 py-2 rounded-lg bg-slate-700 text-white">Stand up</button>
              </div>
            </div>
          )}
          {message && <p className="text-amber-300">{message}</p>}
        </div>
      </main>
    </div>
  );
}
