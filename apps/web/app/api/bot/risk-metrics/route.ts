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
        account_equity::float as account_equity,
        unrealized_pl::float as unrealized_pl
      FROM bot_status
      WHERE bot_name = ${botName}
      ORDER BY last_heartbeat DESC
      LIMIT 1
    `;

    const portfolioValue = Number(botStatus[0]?.account_equity || botStatus[0]?.portfolio_value || 0);
    const openPositions = Number(positions[0]?.count || 0);

    const openRows = await prisma.$queryRaw<any[]>`
      SELECT entry_price::float AS entry_price, stop_loss::float AS stop_loss, quantity::float AS quantity
      FROM positions
      WHERE bot_name = ${botName} AND quantity <> 0
    `;
    const stopsKnown = openRows.length > 0 && openRows.every((row) => row.stop_loss != null);
    let portfolioHeat: number | null = null;
    if (stopsKnown && portfolioValue > 0) {
      const totalRisk = openRows.reduce((sum, row) => {
        return sum + Math.abs(Number(row.entry_price) - Number(row.stop_loss)) * Math.abs(Number(row.quantity));
      }, 0);
      portfolioHeat = totalRisk / portfolioValue;
    }
    const maxPortfolioHeat = 0.10;

    const drawdownRows = await prisma.$queryRaw<any[]>`
      SELECT MAX(max_drawdown)::float AS max_dd
      FROM strategy_performance
      WHERE bot_name = ${botName}
    `;
    const maxDrawdown = Number(drawdownRows[0]?.max_dd || 0) / 100;
    const maxDrawdownLimit = 0.15;

    const dailyRows = await prisma.$queryRaw<any[]>`
      SELECT COALESCE(SUM(pnl), 0)::float AS daily
      FROM trades
      WHERE bot_name = ${botName}
        AND pnl IS NOT NULL
        AND exited_at >= (date_trunc('day', NOW() AT TIME ZONE 'America/New_York') AT TIME ZONE 'America/New_York')
    `;
    const dailyPnl = Number(dailyRows[0]?.daily || 0);
    const dailyLossLimit = portfolioValue * 0.03;
    const positionCaps: Record<string, number> = {
      'quantshift-equity': 10,
      'quantshift-crypto': 8,
      'quantshift-kraken': 6,
    };
    const maxPositions = positionCaps[botName] ?? 10;

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
