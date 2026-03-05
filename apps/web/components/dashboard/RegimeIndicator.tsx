"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Activity, Zap, AlertTriangle } from "lucide-react";

interface RegimeData {
  regime: string;
  method: 'ml' | 'rule_based';
  confidence?: number;
  allocation: {
    BollingerBounce: number;
    RSIMeanReversion: number;
    BreakoutMomentum?: number;
  };
  risk_multiplier: number;
  timestamp: string;
}

export function RegimeIndicator({ botName }: { botName: string }) {
  const [regimeData, setRegimeData] = useState<RegimeData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRegimeData();
    const interval = setInterval(fetchRegimeData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, [botName]);

  const fetchRegimeData = async () => {
    try {
      const res = await fetch(`/api/bot/regime?botName=${botName}`);
      if (res.ok) {
        setRegimeData(await res.json());
      }
    } catch (error) {
      console.error('Failed to fetch regime data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700 animate-pulse">
        <div className="h-20 bg-slate-700/50 rounded" />
      </div>
    );
  }

  if (!regimeData) {
    return (
      <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
        <p className="text-slate-400 text-sm">No regime data available</p>
      </div>
    );
  }

  const getRegimeConfig = (regime: string) => {
    const configs: Record<string, { 
      label: string; 
      color: string; 
      bgGradient: string; 
      borderColor: string; 
      icon: React.ReactNode;
      description: string;
    }> = {
      'BULL_TRENDING': {
        label: 'Bull Trending',
        color: 'text-green-400',
        bgGradient: 'from-green-900/50 to-emerald-900/50',
        borderColor: 'border-green-700/50',
        icon: <TrendingUp className="h-5 w-5 text-green-400" />,
        description: 'Uptrend + low volatility'
      },
      'BEAR_TRENDING': {
        label: 'Bear Trending',
        color: 'text-red-400',
        bgGradient: 'from-red-900/50 to-rose-900/50',
        borderColor: 'border-red-700/50',
        icon: <TrendingDown className="h-5 w-5 text-red-400" />,
        description: 'Downtrend + low volatility'
      },
      'HIGH_VOL_CHOPPY': {
        label: 'High Vol Choppy',
        color: 'text-orange-400',
        bgGradient: 'from-orange-900/50 to-amber-900/50',
        borderColor: 'border-orange-700/50',
        icon: <Activity className="h-5 w-5 text-orange-400" />,
        description: 'High volatility, no clear trend'
      },
      'LOW_VOL_RANGE': {
        label: 'Low Vol Range',
        color: 'text-blue-400',
        bgGradient: 'from-blue-900/50 to-cyan-900/50',
        borderColor: 'border-blue-700/50',
        icon: <Zap className="h-5 w-5 text-blue-400" />,
        description: 'Low volatility, sideways'
      },
      'CRISIS': {
        label: 'Crisis',
        color: 'text-purple-400',
        bgGradient: 'from-purple-900/50 to-pink-900/50',
        borderColor: 'border-purple-700/50',
        icon: <AlertTriangle className="h-5 w-5 text-purple-400" />,
        description: 'Extreme volatility or VIX spike'
      }
    };

    return configs[regime] || {
      label: 'Unknown',
      color: 'text-slate-400',
      bgGradient: 'from-slate-800/50 to-slate-700/50',
      borderColor: 'border-slate-700',
      icon: <Activity className="h-5 w-5 text-slate-400" />,
      description: 'Unknown market regime'
    };
  };

  const config = getRegimeConfig(regimeData.regime);

  return (
    <div className={`bg-gradient-to-br ${config.bgGradient} rounded-xl p-5 border ${config.borderColor}`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-slate-400 text-xs font-medium mb-1">Market Regime</p>
          <div className="flex items-center gap-2">
            {config.icon}
            <h3 className={`text-xl font-bold ${config.color}`}>{config.label}</h3>
          </div>
          <p className="text-slate-400 text-xs mt-1">{config.description}</p>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-xs font-medium text-slate-400">
              {regimeData.method === 'ml' ? 'ML' : 'Rule-Based'}
            </span>
            {regimeData.confidence && (
              <span className={`text-xs font-semibold ${
                regimeData.confidence > 0.8 ? 'text-green-400' : 
                regimeData.confidence > 0.6 ? 'text-yellow-400' : 
                'text-orange-400'
              }`}>
                {(regimeData.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <p className="text-slate-500 text-xs">
            Risk: {(regimeData.risk_multiplier * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-slate-400 text-xs font-medium">Strategy Allocation</p>
        <div className="space-y-1.5">
          {regimeData.allocation && Object.entries(regimeData.allocation).map(([strategy, allocation]) => (
            <div key={strategy} className="flex items-center justify-between">
              <span className="text-slate-300 text-xs">{strategy}</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${config.color.replace('text-', 'bg-')}`}
                    style={{ width: `${allocation * 100}%` }}
                  />
                </div>
                <span className="text-slate-400 text-xs w-10 text-right">
                  {(allocation * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
