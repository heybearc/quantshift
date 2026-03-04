import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const botName = searchParams.get('bot') || 'quantshift-equity';

    // Try to fetch from Redis first (real-time data)
    try {
      const redis = require('redis');
      const client = redis.createClient({
        url: process.env.REDIS_URL || 'redis://10.92.3.21:6379'
      });
      
      await client.connect();
      
      // Fetch risk metrics from Redis
      const riskData = await client.get(`bot:${botName}:risk_metrics`);
      
      await client.quit();
      
      if (riskData) {
        const metrics = JSON.parse(riskData);
        return NextResponse.json(metrics);
      }
    } catch (redisError) {
      console.error('Redis error:', redisError);
    }

    // Fallback to mock data if Redis unavailable
    const mockMetrics = {
      portfolio_heat: 0.0,
      portfolio_heat_pct: 0.0,
      max_heat_limit: 0.10,
      heat_utilization: 0.0,
      daily_pl: 0.0,
      daily_pl_pct: 0.0,
      daily_loss_limit: 0.05,
      drawdown: 0.0,
      max_drawdown_limit: 0.15,
      peak_equity: 100000.0,
      circuit_breaker_status: 'normal',
      circuit_breaker_reason: null,
      num_positions: 0
    };

    return NextResponse.json(mockMetrics);
  } catch (error) {
    console.error('Error fetching risk metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch risk metrics' },
      { status: 500 }
    );
  }
}
