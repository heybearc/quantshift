"use client";

import { useEffect, useState } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";

interface Comment {
  id: string;
  body: string;
  author: string;
}

interface Idea {
  id: string;
  title: string;
  body: string;
  source: string;
  status: string;
  authorId: string;
  author: string;
  comments: Comment[];
}

export default function StrategiesPage() {
  const { user } = useAuth();
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [source, setSource] = useState("human");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");

  const load = () => {
    fetch("/api/strategies")
      .then((response) => response.json())
      .then((data) => setIdeas(data.ideas || []))
      .catch(() => setMessage("Suggestions could not be loaded."));
  };

  useEffect(() => {
    if (user) load();
  }, [user]);

  const suggest = async () => {
    setMessage("");
    const response = await fetch("/api/strategies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, body, source }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "The suggestion was not saved.");
      return;
    }
    setTitle("");
    setBody("");
    load();
  };

  const publish = async (id: string) => {
    setMessage("");
    const response = await fetch(`/api/strategies/${id}/publish`, { method: "POST" });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.error || "The note was not published.");
      return;
    }
    load();
  };

  const tryIdea = async (id: string) => {
    setMessage("");
    const response = await fetch("/api/me/trials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ideaId: id, acceptRisk: true }),
    });
    const data = await response.json();
    setMessage(response.ok ? "Marked on your paper book. It will not send an order until that broker adapter is running." : (data.error || "The strategy was not added."));
  };

  const comment = async (id: string) => {
    const text = drafts[id] || "";
    const response = await fetch(`/api/strategies/${id}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ body: text }),
    });
    if (response.ok) {
      setDrafts({ ...drafts, [id]: "" });
      load();
    }
  };

  if (!user) return null;

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        <ReleaseBanner userId={user.id} />
        <div className="p-8 space-y-6 max-w-3xl">
          <div>
            <h1 className="text-3xl font-bold text-white">Strategy notes</h1>
            <p className="text-slate-400 mt-2">
              Publish a note to offer it to other people, at their own risk, on their own paper book. Publishing does not send an order and it does not change the house books.
            </p>
          </div>
          <div className="space-y-3 bg-slate-800/50 border border-slate-700 rounded-xl p-4">
            <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Title" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white" />
            <textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="What repeated, and on which symbols?" className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white h-28" />
            <div className="flex gap-3">
              <select value={source} onChange={(event) => setSource(event.target.value)} className="bg-slate-900 border border-slate-700 rounded-lg px-3 text-white">
                <option value="human">From a person</option>
                <option value="engine">From the ranker</option>
              </select>
              <button onClick={suggest} className="px-4 py-2 rounded-lg bg-cyan-600 text-white">Post suggestion</button>
            </div>
          </div>
          {message && <p className="text-amber-300">{message}</p>}
          {ideas.map((idea) => (
            <article key={idea.id} className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 space-y-3">
              <div className="flex justify-between gap-4">
                <h2 className="text-white text-lg">{idea.title}</h2>
                <span className="text-slate-400 text-sm">{idea.source} · {idea.status === "published" ? "published, use at your own risk" : "draft"}</span>
              </div>
              <p className="text-slate-300 whitespace-pre-wrap">{idea.body}</p>
              <p className="text-slate-500 text-sm">{idea.author}</p>
              {idea.comments.map((note) => (
                <p key={note.id} className="text-slate-300 text-sm border-t border-slate-700 pt-2">{note.author}: {note.body}</p>
              ))}
              <div className="flex gap-2">
                {idea.authorId === user.id && idea.status !== "published" && (
                  <button onClick={() => publish(idea.id)} className="px-3 py-2 rounded-lg bg-cyan-700 text-white">Publish</button>
                )}
                {idea.status === "published" && (
                  <button onClick={() => tryIdea(idea.id)} className="px-3 py-2 rounded-lg bg-slate-700 text-white">Try on my paper book</button>
                )}
              </div>
              <div className="flex gap-2">
                <input value={drafts[idea.id] || ""} onChange={(event) => setDrafts({ ...drafts, [idea.id]: event.target.value })} placeholder="Add what you see" className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white" />
                <button onClick={() => comment(idea.id)} className="px-3 py-2 rounded-lg bg-slate-700 text-white">Reply</button>
              </div>
            </article>
          ))}
        </div>
      </main>
    </div>
  );
}
