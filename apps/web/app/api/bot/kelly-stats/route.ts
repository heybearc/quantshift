import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: Request) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const botName = searchParams.get('botName') || 'quantshift-equity';

    // Read Kelly stats from Redis
    const Redis = require('ioredis');
    const redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      password: process.env.REDIS_PASSWORD,
    });

    let kellyData = null;
    try {
      const data = await redis.get(`bot:${botName}:kelly_stats`);
      if (data) {
        kellyData = JSON.parse(data);
      }
    } catch (redisError) {
      console.error('Redis error:', redisError);
    } finally {
      redis.disconnect();
    }

    // Fallback to mock data if Redis unavailable
    if (!kellyData) {
      // Fetch trade count from database to determine if we have enough data
      let tradeCount = 0;
      try {
        const { Pool } = require('pg');
        const pool = new Pool({
          host: process.env.DATABASE_HOST || 'localhost',
          port: parseInt(process.env.DATABASE_PORT || '5432'),
          database: process.env.DATABASE_NAME || 'quantshift',
          user: process.env.DATABASE_USER || 'quantshift',
          password: process.env.DATABASE_PASSWORD,
        });

        const result = await pool.query(
          `SELECT COUNT(*) as count FROM trades WHERE bot_name = $1 AND exit_time IS NOT NULL`,
          [botName]
        );

        tradeCount = parseInt(result.rows[0]?.count || '0');
        await pool.end();
      } catch (dbError) {
        console.error('Database error:', dbError);
      }

      kellyData = {
        enabled: false,
        kelly_percentage: 0,
        kelly_fraction: 0.25,
        min_trades_required: 20,
        current_trades: tradeCount,
        win_rate: 0,
        avg_win: 0,
        avg_loss: 0,
        recommended_size_pct: 0.01,
        fallback_size_pct: 0.01,
        using_fallback: true,
        reason: 'Kelly Criterion disabled in configuration',
      };
    }

    return NextResponse.json(kellyData);
  } catch (error) {
    console.error('Error fetching Kelly stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch Kelly stats' },
      { status: 500 }
    );
  }
}
