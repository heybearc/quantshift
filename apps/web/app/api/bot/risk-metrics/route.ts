import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const searchParams = request.nextUrl.searchParams;
    const botName = searchParams.get('bot') || 'quantshift-equity';

    // Fetch from database with proper type conversion
    const positions = await prisma.$queryRaw<any[]>`
      SELECT COUNT(*)::int as count, COALESCE(SUM(unrealized_pl), 0)::float as total_unrealized_pl
      FROM positions
      WHERE quantity > 0 AND bot_name = ${botName}
    `;

    const botStatus = await prisma.$queryRaw<any[]>`
      SELECT 
        portfolio_value::float as portfolio_value, 
        unrealized_pl::float as unrealized_pl, 
        realized_pl::float as realized_pl
      FROM bot_status
      WHERE bot_name = ${botName}
      ORDER BY last_heartbeat DESC
      LIMIT 1
    `;

    const portfolioValue = Number(botStatus[0]?.portfolio_value || 100000);
    const unrealizedPl = Number(botStatus[0]?.unrealized_pl || 0);
    const openPositions = Number(positions[0]?.count || 0);

    // Calculate metrics
    const portfolioHeat = portfolioValue > 0 ? Math.abs(unrealizedPl) / portfolioValue : 0;
    const maxPortfolioHeat = 0.10; // 10% max
    const maxDrawdown = 0.0; // TODO: Calculate from trade history
    const maxDrawdownLimit = 0.15; // 15% max
    const dailyPnl = Number(botStatus[0]?.realized_pl || 0);
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

    return NextResponse.json(metrics);
  } catch (error) {
    console.error('Error fetching risk metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch risk metrics' },
      { status: 500 }
    );
  }
}
