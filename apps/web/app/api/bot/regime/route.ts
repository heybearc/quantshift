import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const botName = searchParams.get('bot') || searchParams.get('botName') || 'quantshift-equity';

    // Fetch regime data from database (primary source)
    let current = null;
    
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
        `SELECT regime, method, confidence, risk_multiplier, allocation, timestamp,
                trend_slope, volatility, market_breadth, vix
         FROM regime_history 
         WHERE bot_name = $1 
         ORDER BY timestamp DESC 
         LIMIT 1`,
        [botName]
      ).catch(() => pool.query(
        `SELECT regime, method, confidence, risk_multiplier, allocation, timestamp
         FROM regime_history 
         WHERE bot_name = $1 
         ORDER BY timestamp DESC 
         LIMIT 1`,
        [botName]
      ));

      if (currentResult.rows.length > 0) {
        const row = currentResult.rows[0];
        current = {
          regime: row.regime,
          method: row.method,
          confidence: row.confidence,
          risk_multiplier: row.risk_multiplier,
          allocation: typeof row.allocation === 'string' ? JSON.parse(row.allocation) : row.allocation,
          timestamp: row.timestamp,
          trend: row.trend_slope ?? null,
          volatility: row.volatility ?? null,
          marketBreadth: row.market_breadth ?? null,
          vix: row.vix ?? null,
        };
      }

      await pool.end();
    } catch (dbError) {
      console.error('Database error fetching regime data:', dbError);
    }

    if (!current) {
      return NextResponse.json({ regime: null });
    }

    return NextResponse.json({
      regime: current.regime,
      confidence: current.confidence,
      trend: current.trend ?? null,
      volatility: current.volatility ?? null,
      marketBreadth: current.marketBreadth ?? null,
      vix: current.vix ?? null,
      method: current.method,
      riskMultiplier: current.risk_multiplier || 1.0,
      risk_multiplier: current.risk_multiplier || 1.0,
      allocation: current.allocation,
      timestamp: current.timestamp,
    });
  } catch (error) {
    console.error('Error fetching regime data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch regime data' },
      { status: 500 }
    );
  }
}

