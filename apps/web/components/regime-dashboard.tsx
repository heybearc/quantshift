'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, TrendingUp, Activity, BarChart3 } from 'lucide-react';

interface RegimeData {
  current: {
    regime: string;
    method: string;
    confidence: number;
    riskMultiplier: number;
    allocation: Record<string, number>;
    timestamp: string;
  };
  history: Array<{
    timestamp: string;
    regime: string;
    confidence: number;
    method: string;
  }>;
  stats: {
    totalChanges: number;
    averageConfidence: number;
    regimeDistribution: Record<string, number>;
  };
  mlModel: {
    accuracy: number;
    trainDate: string;
    features: Array<{
      name: string;
      importance: number;
    }>;
  };
}

const regimeColors: Record<string, string> = {
  BULL_TRENDING: 'bg-green-500',
  BEAR_TRENDING: 'bg-red-500',
  HIGH_VOL_CHOPPY: 'bg-orange-500',
  LOW_VOL_RANGE: 'bg-blue-500',
  CRISIS: 'bg-purple-500',
  UNKNOWN: 'bg-gray-500',
};

const regimeLabels: Record<string, string> = {
  BULL_TRENDING: 'Bull Trending',
  BEAR_TRENDING: 'Bear Trending',
  HIGH_VOL_CHOPPY: 'High Vol Choppy',
  LOW_VOL_RANGE: 'Low Vol Range',
  CRISIS: 'Crisis',
  UNKNOWN: 'Unknown',
};

export function RegimeDashboard() {
  const [data, setData] = useState<RegimeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRegimeData();
    const interval = setInterval(fetchRegimeData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchRegimeData = async () => {
    try {
      const response = await fetch('/api/bot/regime');
      if (!response.ok) throw new Error('Failed to fetch regime data');
      const regimeData = await response.json();
      setData(regimeData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="animate-pulse">
          <CardHeader className="h-32 bg-muted" />
        </Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Error Loading Regime Data</CardTitle>
          <CardDescription>{error || 'No data available'}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const { current, stats, mlModel } = data;

  return (
    <div className="space-y-4">
      {/* Header Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Current Regime */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Regime</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${regimeColors[current.regime]}`} />
              <div className="text-2xl font-bold">{regimeLabels[current.regime]}</div>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline" className="text-xs">
                {current.method === 'ml' ? (
                  <><Brain className="h-3 w-3 mr-1" /> ML Predicted</>
                ) : (
                  'Rule-Based'
                )}
              </Badge>
              <p className="text-xs text-muted-foreground">
                {(current.confidence * 100).toFixed(1)}% confidence
              </p>
            </div>
          </CardContent>
        </Card>

        {/* ML Model Accuracy */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ML Model Accuracy</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(mlModel.accuracy * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Test accuracy on 2 years of data
            </p>
            <p className="text-xs text-muted-foreground">
              Trained: {new Date(mlModel.trainDate).toLocaleDateString()}
            </p>
          </CardContent>
        </Card>

        {/* Risk Multiplier */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Multiplier</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {current.riskMultiplier.toFixed(2)}x
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Position sizing adjustment
            </p>
          </CardContent>
        </Card>

        {/* Regime Changes */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Regime Changes</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalChanges}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Last 7 days
            </p>
            <p className="text-xs text-muted-foreground">
              Avg confidence: {(stats.averageConfidence * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Strategy Allocation */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Allocation by Regime</CardTitle>
          <CardDescription>
            Current capital allocation based on {regimeLabels[current.regime]} regime
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(current.allocation).map(([strategy, allocation]) => (
              <div key={strategy} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{strategy}</span>
                  <span className="text-muted-foreground">
                    {(allocation * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${allocation * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ML Feature Importance */}
      <Card>
        <CardHeader>
          <CardTitle>ML Model Feature Importance</CardTitle>
          <CardDescription>
            Top features used by the RandomForest classifier
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mlModel.features.map((feature) => (
              <div key={feature.name} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium capitalize">
                    {feature.name.replace(/_/g, ' ')}
                  </span>
                  <span className="text-muted-foreground">
                    {(feature.importance * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${feature.importance * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Regime Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Regime Distribution (7 Days)</CardTitle>
          <CardDescription>
            Percentage of time spent in each market regime
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(stats.regimeDistribution)
              .sort(([, a], [, b]) => b - a)
              .map(([regime, percentage]) => (
                <div key={regime} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className={`h-3 w-3 rounded-full ${regimeColors[regime]}`} />
                      <span className="font-medium">{regimeLabels[regime]}</span>
                    </div>
                    <span className="text-muted-foreground">{percentage}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${regimeColors[regime]} transition-all`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
