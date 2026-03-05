import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const botName = searchParams.get('bot') || 'quantshift-equity';

    // Fetch regime data from database (primary source)
    let current = null;
    let history = [];
    
    try {
      const { Pool } = require('pg');
      const pool = new Pool({
        host: process.env.DATABASE_HOST || '10.92.3.21',
        port: parseInt(process.env.DATABASE_PORT || '5432'),
        database: process.env.DATABASE_NAME || 'quantshift',
        user: process.env.DATABASE_USER || 'quantshift',
        password: process.env.DATABASE_PASSWORD,
      });

      // Get most recent regime data for current state
      const currentResult = await pool.query(
        `SELECT regime, method, confidence, risk_multiplier, allocation, timestamp 
         FROM regime_history 
         WHERE bot_name = $1 
         ORDER BY timestamp DESC 
         LIMIT 1`,
        [botName]
      );

      if (currentResult.rows.length > 0) {
        const row = currentResult.rows[0];
        current = {
          regime: row.regime,
          method: row.method,
          confidence: row.confidence,
          risk_multiplier: row.risk_multiplier,
          allocation: typeof row.allocation === 'string' ? JSON.parse(row.allocation) : row.allocation,
          timestamp: row.timestamp,
        };
      }

      // Get regime history
      const historyResult = await pool.query(
        `SELECT regime, method, confidence, risk_multiplier, allocation, timestamp 
         FROM regime_history 
         WHERE bot_name = $1 
         AND timestamp > NOW() - INTERVAL '30 days'
         ORDER BY timestamp DESC 
         LIMIT 100`,
        [botName]
      );

      history = historyResult.rows.map((row: any) => ({
        timestamp: row.timestamp,
        regime: row.regime,
        confidence: row.confidence,
        method: row.method,
        riskMultiplier: row.risk_multiplier,
        allocation: typeof row.allocation === 'string' ? JSON.parse(row.allocation) : row.allocation,
      }));

      await pool.end();
    } catch (dbError) {
      console.error('Database error fetching regime data:', dbError);
    }

    // Fallback to mock data if database unavailable or no data
    if (!current) {
      current = {
        regime: 'LOW_VOL_RANGE',
        method: 'ml',
        confidence: 0.5,
        risk_multiplier: 1.0,
        allocation: {
          BollingerBounce: 0.60,
          RSIMeanReversion: 0.40,
          Breakout: 0.0,
        },
        timestamp: new Date().toISOString(),
      };
    }

    if (history.length === 0) {
      history = generateMockHistory(7);
    }

    // Convert snake_case to camelCase for frontend
    const currentFormatted = {
      regime: current.regime,
      method: current.method,
      confidence: current.confidence,
      riskMultiplier: current.risk_multiplier || 1.0,
      allocation: current.allocation,
      timestamp: current.timestamp,
    };

    return NextResponse.json({
      current: currentFormatted,
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
