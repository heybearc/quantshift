import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: Request) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const botName = searchParams.get('bot') || 'equity-bot';

    // TODO: Read from Redis bot state when available
    // For now, return mock data showing ML regime classifier is active
    
    // Simulated current regime data
    const current = {
      regime: 'BULL_TRENDING',
      method: 'ml',
      confidence: 0.917, // ML model accuracy
      riskMultiplier: 1.0,
      allocation: {
        BollingerBounce: 0.30,
        RSIMeanReversion: 0.20,
        Breakout: 0.50,
      },
      timestamp: new Date().toISOString(),
    };

    // Simulated 7-day history
    const history = generateMockHistory(7);

    return NextResponse.json({
      current,
      history,
      stats: {
        totalChanges: calculateRegimeChanges(history),
        averageConfidence: calculateAverageConfidence(history),
        regimeDistribution: calculateRegimeDistribution(history),
      },
      mlModel: {
        accuracy: 0.917,
        trainDate: '2026-02-21T23:42:31Z',
        features: [
          { name: 'atr_ratio', importance: 0.294 },
          { name: 'sma_50_slope', importance: 0.221 },
          { name: 'sma_200_slope', importance: 0.205 },
          { name: 'macd_signal', importance: 0.092 },
          { name: 'macd', importance: 0.057 },
        ],
      },
    });
  } catch (error) {
    console.error('Error fetching regime data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch regime data' },
      { status: 500 }
    );
  }
}

function generateMockHistory(days: number) {
  const regimes = ['BULL_TRENDING', 'LOW_VOL_RANGE', 'HIGH_VOL_CHOPPY'];
  const history = [];
  const now = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    history.push({
      timestamp: date.toISOString(),
      regime: regimes[Math.floor(Math.random() * regimes.length)],
      confidence: 0.85 + Math.random() * 0.15, // 85-100%
      method: 'ml',
    });
  }

  return history;
}

function calculateRegimeChanges(history: any[]): number {
  let changes = 0;
  for (let i = 1; i < history.length; i++) {
    if (history[i].regime !== history[i - 1].regime) {
      changes++;
    }
  }
  return changes;
}

function calculateAverageConfidence(history: any[]): number {
  const confidences = history
    .map((h: any) => h.confidence)
    .filter((c: any) => c !== null && c !== undefined);
  
  if (confidences.length === 0) return 0;
  
  return confidences.reduce((sum: number, c: number) => sum + c, 0) / confidences.length;
}

function calculateRegimeDistribution(history: any[]): Record<string, number> {
  const distribution: Record<string, number> = {};
  
  history.forEach((entry: any) => {
    const regime = entry.regime;
    distribution[regime] = (distribution[regime] || 0) + 1;
  });
  
  // Convert to percentages
  const total = history.length;
  Object.keys(distribution).forEach((key) => {
    distribution[key] = Math.round((distribution[key] / total) * 100);
  });
  
  return distribution;
}
