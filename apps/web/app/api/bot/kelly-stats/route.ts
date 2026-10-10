import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const botName = new URL(request.url).searchParams.get('botName') || 'quantshift-equity';
    const closedTrades = await prisma.trade.findMany({
      where: { botName, status: 'CLOSED' },
      select: { pnl: true },
    });

    const withPnl = closedTrades.filter((trade) => trade.pnl != null);
    const wins = withPnl.filter((trade) => (trade.pnl ?? 0) > 0);
    const losses = withPnl.filter((trade) => (trade.pnl ?? 0) < 0);
    const avgWin = wins.length
      ? wins.reduce((sum, trade) => sum + (trade.pnl ?? 0), 0) / wins.length
      : 0;
    const avgLoss = losses.length
      ? Math.abs(losses.reduce((sum, trade) => sum + (trade.pnl ?? 0), 0) / losses.length)
      : 0;
    const winRate = withPnl.length ? wins.length / withPnl.length : 0;

    return NextResponse.json({
      enabled: false,
      kelly_percentage: 0,
      kelly_fraction: 0.25,
      min_trades_required: 20,
      current_trades: closedTrades.length,
      win_rate: winRate,
      avg_win: avgWin,
      avg_loss: avgLoss,
      recommended_size_pct: 0.01,
      fallback_size_pct: 0.01,
      using_fallback: true,
      reason: 'Kelly sizing stays off until it is enabled after 20 closed trades',
    });
  } catch (error) {
    console.error('Error fetching Kelly stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch Kelly stats' },
      { status: 500 }
    );
  }
}
