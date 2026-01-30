import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface TrendIndicatorProps {
  value: number;
  showPercentage?: boolean;
  size?: 'sm' | 'md';
}

export function TrendIndicator({ value, showPercentage = true, size = 'sm' }: TrendIndicatorProps) {
  const isPositive = value > 0;
  const isNeutral = value === 0;
  
  const iconSize = size === 'sm' ? 'h-3 w-3' : 'h-4 w-4';
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';
  
  const getColor = () => {
    if (isNeutral) return 'text-slate-400';
    return isPositive ? 'text-green-400' : 'text-red-400';
  };

  const getIcon = () => {
    if (isNeutral) return <Minus className={iconSize} />;
    return isPositive ? <TrendingUp className={iconSize} /> : <TrendingDown className={iconSize} />;
  };

  const formatValue = () => {
    const absValue = Math.abs(value);
    if (showPercentage) {
      return `${isPositive ? '+' : '-'}${absValue.toFixed(1)}%`;
    }
    return `${isPositive ? '+' : '-'}${absValue.toFixed(0)}`;
  };

  return (
    <div className={`flex items-center gap-1 ${getColor()} ${textSize}`}>
      {getIcon()}
      <span>{formatValue()}</span>
    </div>
  );
}
