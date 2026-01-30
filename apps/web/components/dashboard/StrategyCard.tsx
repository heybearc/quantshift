import { Zap, TrendingUp } from "lucide-react";

interface StrategyCardProps {
  currentStrategy: string;
  strategySuccessRate: number;
  avgTradesPerDay: number;
}

export function StrategyCard({ currentStrategy, strategySuccessRate, avgTradesPerDay }: StrategyCardProps) {
  const isSuccessful = strategySuccessRate >= 50;

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-400 text-sm">Strategy</span>
        <Zap className="h-5 w-5 text-cyan-500" />
      </div>
      <p className="text-xl font-bold text-white mb-1 truncate">
        {currentStrategy}
      </p>
      <div className="flex items-center gap-2 text-sm">
        <span className={isSuccessful ? "text-green-400" : "text-red-400"}>
          {strategySuccessRate.toFixed(1)}% success
        </span>
        <span className="text-slate-500">•</span>
        <span className="text-slate-400">
          {avgTradesPerDay.toFixed(1)}/day
        </span>
      </div>
    </div>
  );
}
