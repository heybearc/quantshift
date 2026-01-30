interface PercentageChangeProps {
  value: number;
  label?: string;
}

export function PercentageChange({ value, label }: PercentageChangeProps) {
  const isPositive = value > 0;
  const isNeutral = value === 0;
  
  const getColor = () => {
    if (isNeutral) return 'bg-slate-700 text-slate-300';
    return isPositive ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400';
  };

  const formatValue = () => {
    const absValue = Math.abs(value);
    return `${isPositive ? '+' : isNeutral ? '' : '-'}${absValue.toFixed(1)}%`;
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getColor()}`}>
      {formatValue()}
      {label && <span className="ml-1 text-slate-400">{label}</span>}
    </span>
  );
}
