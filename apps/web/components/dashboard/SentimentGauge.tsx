'use client';

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface SentimentGaugeProps {
  score: number; // -1.0 to +1.0
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function SentimentGauge({ 
  score, 
  label, 
  size = 'md',
  showLabel = true 
}: SentimentGaugeProps) {
  // Normalize score to 0-100 for gauge display
  const normalizedScore = ((score + 1) / 2) * 100;
  
  // Determine sentiment category
  const getSentimentInfo = () => {
    if (score > 0.3) {
      return {
        label: label || 'Positive',
        color: 'text-green-400',
        bgColor: 'bg-green-500/20',
        borderColor: 'border-green-500/50',
        icon: TrendingUp,
        gaugeColor: 'from-green-600 to-green-400'
      };
    } else if (score < -0.3) {
      return {
        label: label || 'Negative',
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-500/50',
        icon: TrendingDown,
        gaugeColor: 'from-red-600 to-red-400'
      };
    } else {
      return {
        label: label || 'Neutral',
        color: 'text-slate-400',
        bgColor: 'bg-slate-500/20',
        borderColor: 'border-slate-500/50',
        icon: Minus,
        gaugeColor: 'from-slate-600 to-slate-400'
      };
    }
  };

  const sentiment = getSentimentInfo();
  const Icon = sentiment.icon;

  const sizeClasses = {
    sm: 'h-16 w-16',
    md: 'h-24 w-24',
    lg: 'h-32 w-32'
  };

  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6'
  };

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Circular Gauge */}
      <div className={`relative ${sizeClasses[size]}`}>
        {/* Background circle */}
        <svg className="transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-slate-700"
          />
          {/* Sentiment arc */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="url(#gradient)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${normalizedScore * 2.827} 282.7`}
            className="transition-all duration-500"
          />
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" className={`${sentiment.gaugeColor.split(' ')[0].replace('from-', 'stop-color-')}`} />
              <stop offset="100%" className={`${sentiment.gaugeColor.split(' ')[1].replace('to-', 'stop-color-')}`} />
            </linearGradient>
          </defs>
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <Icon className={`${iconSizes[size]} ${sentiment.color}`} />
          <span className={`text-xs font-bold ${sentiment.color} mt-1`}>
            {score > 0 ? '+' : ''}{(score * 100).toFixed(0)}
          </span>
        </div>
      </div>

      {/* Label */}
      {showLabel && (
        <div className={`px-3 py-1 rounded-full ${sentiment.bgColor} border ${sentiment.borderColor}`}>
          <span className={`text-xs font-medium ${sentiment.color}`}>
            {sentiment.label}
          </span>
        </div>
      )}
    </div>
  );
}
