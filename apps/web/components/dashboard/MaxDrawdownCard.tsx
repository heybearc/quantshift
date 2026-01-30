import { TrendingDown, AlertTriangle } from "lucide-react";

interface MaxDrawdownCardProps {
  maxDrawdown: number;
  maxDrawdownAmount: number;
  formatCurrency: (value: number) => string;
}

export function MaxDrawdownCard({ maxDrawdown, maxDrawdownAmount, formatCurrency }: MaxDrawdownCardProps) {
  const getSeverityColor = () => {
    if (maxDrawdown === 0) return "text-slate-400";
    if (maxDrawdown < 10) return "text-yellow-500";
    if (maxDrawdown < 20) return "text-orange-500";
    return "text-red-500";
  };

  const getSeverityIcon = () => {
    if (maxDrawdown === 0) return <TrendingDown className="h-5 w-5 text-slate-400" />;
    if (maxDrawdown < 20) return <TrendingDown className="h-5 w-5 text-yellow-500" />;
    return <AlertTriangle className="h-5 w-5 text-red-500" />;
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-5 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-400 text-sm">Max Drawdown</span>
        {getSeverityIcon()}
      </div>
      <p className={`text-3xl font-bold mb-2 ${getSeverityColor()}`}>
        {maxDrawdown === 0 ? "0.0%" : `-${maxDrawdown.toFixed(1)}%`}
      </p>
      <p className="text-sm text-slate-400">
        {maxDrawdownAmount === 0 ? "No drawdown" : formatCurrency(Math.abs(maxDrawdownAmount))}
      </p>
    </div>
  );
}
