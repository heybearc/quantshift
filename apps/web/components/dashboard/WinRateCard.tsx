import { Target, TrendingUp, TrendingDown } from "lucide-react";

interface WinRateCardProps {
  winRate: number;
  totalWins: number;
  totalLosses: number;
  totalTrades: number;
}

export function WinRateCard({ winRate, totalWins, totalLosses, totalTrades }: WinRateCardProps) {
  const isPositive = winRate >= 50;
  
  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-400 text-sm">Win Rate</span>
        {isPositive ? (
          <Target className="h-5 w-5 text-green-500" />
        ) : (
          <Target className="h-5 w-5 text-red-500" />
        )}
      </div>
      <p className={`text-3xl font-bold mb-2 ${isPositive ? "text-green-500" : "text-red-500"}`}>
        {winRate.toFixed(1)}%
      </p>
      <div className="flex items-center gap-2 text-sm">
        <span className="text-green-400">{totalWins}W</span>
        <span className="text-slate-500">/</span>
        <span className="text-red-400">{totalLosses}L</span>
        <span className="text-slate-500">•</span>
        <span className="text-slate-400">{totalTrades} total</span>
      </div>
    </div>
  );
}
