'use client';

import { useEffect, useState } from 'react';
import { Brain, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { SentimentGauge } from './SentimentGauge';

interface SentimentData {
  [symbol: string]: {
    score: number;
    label: string;
    confidence: number;
    articles: number;
    updated: string;
  };
}

export function SentimentOverview() {
  const [sentiment, setSentiment] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSentiment = async () => {
    try {
      const response = await fetch('/api/sentiment');
      if (!response.ok) throw new Error('Failed to fetch sentiment');
      const data = await response.json();
      setSentiment(data.sentiment || {});
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSentiment();
    const interval = setInterval(fetchSentiment, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Market Sentiment</h3>
        </div>
        <div className="text-sm text-slate-400">Loading sentiment data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Market Sentiment</h3>
        </div>
        <div className="text-sm text-red-400">Failed to load sentiment data</div>
      </div>
    );
  }

  if (!sentiment || Object.keys(sentiment).length === 0) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Market Sentiment</h3>
          <span className="text-xs text-slate-400 ml-2">FinBERT AI Analysis</span>
        </div>
        <div className="text-sm text-slate-400">
          No sentiment data available yet. Sentiment analysis will appear when bots generate trading signals.
        </div>
      </div>
    );
  }

  // Calculate overall market sentiment
  const scores = Object.values(sentiment).map(s => s.score);
  const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
  const positiveCount = scores.filter(s => s > 0.3).length;
  const negativeCount = scores.filter(s => s < -0.3).length;

  // Get top symbols by sentiment
  const sortedSymbols = Object.entries(sentiment)
    .sort(([, a], [, b]) => Math.abs(b.score) - Math.abs(a.score))
    .slice(0, 6);

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Market Sentiment</h3>
          <span className="text-xs text-slate-400 ml-2">FinBERT AI Analysis</span>
        </div>
        <button
          onClick={fetchSentiment}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400 hover:text-white"
          title="Refresh sentiment"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Overall Market Sentiment */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="flex flex-col items-center justify-center p-4 rounded-lg bg-slate-900/50 border border-slate-700">
          <SentimentGauge score={avgScore} label="Market" size="md" />
        </div>

        <div className="flex flex-col justify-center gap-3 p-4 rounded-lg bg-slate-900/50 border border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-400" />
              <span className="text-sm text-slate-400">Positive</span>
            </div>
            <span className="text-lg font-bold text-green-400">{positiveCount}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-red-400" />
              <span className="text-sm text-slate-400">Negative</span>
            </div>
            <span className="text-lg font-bold text-red-400">{negativeCount}</span>
          </div>
        </div>

        <div className="flex flex-col justify-center p-4 rounded-lg bg-slate-900/50 border border-slate-700">
          <div className="text-xs text-slate-400 mb-1">Total Symbols</div>
          <div className="text-2xl font-bold text-white">{Object.keys(sentiment).length}</div>
          <div className="text-xs text-slate-400 mt-2">
            Avg {Object.values(sentiment).reduce((a, b) => a + b.articles, 0) / Object.keys(sentiment).length | 0} articles/symbol
          </div>
        </div>
      </div>

      {/* Top Symbols */}
      <div>
        <h4 className="text-sm font-medium text-slate-300 mb-3">Symbol Sentiment</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {sortedSymbols.map(([symbol, data]) => (
            <div
              key={symbol}
              className="p-3 rounded-lg bg-slate-900/50 border border-slate-700 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">{symbol}</span>
                <span className={`text-xs font-bold ${
                  data.score > 0.3 ? 'text-green-400' : 
                  data.score < -0.3 ? 'text-red-400' : 
                  'text-slate-400'
                }`}>
                  {data.score > 0 ? '+' : ''}{(data.score * 100).toFixed(0)}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>{data.articles} articles</span>
                <span>{(data.confidence * 100).toFixed(0)}% conf</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
