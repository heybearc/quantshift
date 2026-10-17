export interface PerformanceBook {
  account: number;
  start: number | null;
  fromStart: number | null;
  closedPnl: number;
  openPnl: number;
  result: number;
}

const BOOKS = [
  { id: "quantshift-equity", label: "Equity" },
  { id: "quantshift-crypto", label: "Crypto" },
  { id: "quantshift-kraken", label: "Kraken" },
] as const;

function signed(value: number, fmt: (value: number) => string) {
  const text = `${value >= 0 ? "+" : ""}${fmt(value)}`;
  return <span className={value >= 0 ? "text-green-400" : "text-red-400"}>{text}</span>;
}

export function PerformanceBooks({
  books,
  formatCurrency,
}: {
  books: { closedPnl: number; openPnl: number; result: number; byBot: Record<string, PerformanceBook> };
  formatCurrency: (value: number) => string;
}) {
  const rows = BOOKS.flatMap(({ id, label }) => {
    const book = books.byBot[id];
    return book ? [{ label, book }] : [];
  });

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-700">
        <p className="text-white font-semibold">Performance</p>
        <p className="text-slate-400 text-xs mt-1">Closed trades plus the open book. Crypto and Kraken also show the account against the paper start.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-500 text-xs">
              <th className="text-left font-medium px-5 py-3">Book</th>
              <th className="text-right font-medium px-3 py-3">Account</th>
              <th className="text-right font-medium px-3 py-3">From start</th>
              <th className="text-right font-medium px-3 py-3">Closed</th>
              <th className="text-right font-medium px-3 py-3">Open</th>
              <th className="text-right font-medium px-5 py-3">Result</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ label, book }) => (
              <tr key={label} className="border-t border-slate-700/80">
                <td className="px-5 py-3 text-white">{label}</td>
                <td className="px-3 py-3 text-right text-slate-200">{formatCurrency(book.account)}</td>
                <td className="px-3 py-3 text-right">
                  {book.fromStart == null ? <span className="text-slate-500">—</span> : signed(book.fromStart, formatCurrency)}
                </td>
                <td className="px-3 py-3 text-right">{signed(book.closedPnl, formatCurrency)}</td>
                <td className="px-3 py-3 text-right">{signed(book.openPnl, formatCurrency)}</td>
                <td className="px-5 py-3 text-right font-semibold">{signed(book.result, formatCurrency)}</td>
              </tr>
            ))}
            <tr className="border-t border-slate-600">
              <td className="px-5 py-3 text-white font-semibold">Total</td>
              <td className="px-3 py-3 text-right text-white font-semibold">
                {formatCurrency(rows.reduce((sum, row) => sum + row.book.account, 0))}
              </td>
              <td className="px-3 py-3 text-right text-slate-500">—</td>
              <td className="px-3 py-3 text-right font-semibold">{signed(books.closedPnl, formatCurrency)}</td>
              <td className="px-3 py-3 text-right font-semibold">{signed(books.openPnl, formatCurrency)}</td>
              <td className="px-5 py-3 text-right font-semibold">{signed(books.result, formatCurrency)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
