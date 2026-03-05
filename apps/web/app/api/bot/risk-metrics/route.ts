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

    // Fallback to database query if Redis unavailable
    const { PrismaClient } = require('@prisma/client');
    const prisma = new PrismaClient();

    const positions = await prisma.$queryRaw<any[]>`
      SELECT COUNT(*) as count, SUM(unrealized_pl) as total_unrealized_pl
      FROM positions
      WHERE quantity > 0
    `;

    const botStatus = await prisma.$queryRaw<any[]>`
      SELECT portfolio_value, unrealized_pl, realized_pl
      FROM bot_status
      LIMIT 1
    `;

    const portfolioValue = botStatus[0]?.portfolio_value || 100000;
    const unrealizedPl = botStatus[0]?.unrealized_pl || 0;
    const openPositions = positions[0]?.count || 0;

    // Calculate metrics
    const portfolioHeat = portfolioValue > 0 ? Math.abs(unrealizedPl) / portfolioValue : 0;
    const maxPortfolioHeat = 0.10; // 10% max
    const maxDrawdown = 0.0; // TODO: Calculate from trade history
    const maxDrawdownLimit = 0.15; // 15% max
    const dailyPnl = botStatus[0]?.realized_pl || 0;
    const dailyLossLimit = portfolioValue * 0.03; // 3% daily loss limit
    const maxPositions = 5;

    const metrics = {
      portfolioHeat,
      maxPortfolioHeat,
      maxDrawdown,
      maxDrawdownLimit,
      dailyPnl,
      dailyLossLimit,
      openPositions,
      maxPositions,
    };

    await prisma.$disconnect();
    return NextResponse.json(metrics);
  } catch (error) {
    console.error('Error fetching risk metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch risk metrics' },
      { status: 500 }
    );
  }
}
