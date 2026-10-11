import { TrendingDown, AlertTriangle } from "lucide-react";

interface MaxDrawdownCardProps {
  maxDrawdown: number | null;
  maxDrawdownAmount: number | null;
  formatCurrency: (value: number) => string;
}

export function MaxDrawdownCard({ maxDrawdown, maxDrawdownAmount, formatCurrency }: MaxDrawdownCardProps) {
  const recorded = maxDrawdown != null;
  const drawdown = maxDrawdown ?? 0;

  const getSeverityColor = () => {
    if (!recorded || drawdown === 0) return "text-slate-400";
    if (drawdown < 10) return "text-yellow-500";
    if (drawdown < 20) return "text-orange-500";
    return "text-red-500";
  };

  const getSeverityIcon = () => {
    if (!recorded || drawdown === 0) return <TrendingDown className="h-5 w-5 text-slate-400" />;
    if (drawdown < 20) return <TrendingDown className="h-5 w-5 text-yellow-500" />;
    return <AlertTriangle className="h-5 w-5 text-red-500" />;
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-400 text-sm">Max Drawdown</span>
        {getSeverityIcon()}
      </div>
      <p className={`text-3xl font-bold mb-2 ${getSeverityColor()}`}>
        {!recorded ? "—" : drawdown === 0 ? "0.0%" : `-${drawdown.toFixed(1)}%`}
      </p>
      <p className="text-sm text-slate-400">
        {!recorded || maxDrawdownAmount == null ? "Not recorded" : maxDrawdownAmount === 0 ? "No drawdown" : formatCurrency(Math.abs(maxDrawdownAmount))}
      </p>
    </div>
  );
}
