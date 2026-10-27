"use client";

import { useEffect, useState } from "react";

type QuietBook = {
  botName: string;
  checked: number;
  unfinished: number;
  noSqueeze: number;
  noPivot: number;
  alreadyOpen: number;
  passed: number;
  updated: string | null;
  examples: { symbol: string; reason: string }[];
};

const LABELS: Record<string, string> = {
  "quantshift-crypto": "Coinbase",
  "quantshift-kraken": "Kraken",
};

export function QuietHour() {
  const [books, setBooks] = useState<QuietBook[]>([]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const response = await fetch("/api/bot/quiet-hour");
        if (!response.ok) return;
        const data = await response.json();
        if (!cancelled) setBooks(data.books || []);
      } catch {
        // The next refresh can try again.
      }
    };
    load();
    const timer = setInterval(load, 60_000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  if (books.length === 0) return null;

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-5">
      <p className="text-white font-semibold">Quiet hour</p>
      <p className="text-slate-400 text-xs mt-1">
        Why the volatility break stayed flat. A finished hour, a squeeze, and a pivot break are still required.
      </p>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {books.map((book) => (
          <div key={book.botName} className="rounded-lg border border-slate-700 p-4">
            <p className="text-sm font-medium text-white">{LABELS[book.botName] || book.botName}</p>
            <p className="text-xs text-slate-400 mt-1">{book.checked} names checked</p>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-300">
              <div>Hour still open: {book.unfinished}</div>
              <div>No squeeze: {book.noSqueeze}</div>
              <div>No pivot break: {book.noPivot}</div>
              <div>Already open: {book.alreadyOpen}</div>
            </dl>
            {book.examples[0] && (
              <p className="text-xs text-slate-500 mt-3">
                {book.examples[0].symbol}: {book.examples[0].reason}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
