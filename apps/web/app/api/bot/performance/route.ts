import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const days = parseInt(searchParams.get('days') || '30');

    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const botName = searchParams.get('botName');
    const where: any = { date: { gte: startDate } };
    if (botName) where.botName = botName;

    const metrics = await prisma.performanceMetrics.findMany({
      where,
      orderBy: { date: 'asc' },
    });

    const closed = await prisma.trade.findMany({
      where: {
        pnl: { not: null },
        exitedAt: { gte: startDate },
        ...(botName ? { botName } : {}),
      },
      orderBy: { exitedAt: 'asc' },
      select: { exitedAt: true, pnl: true },
    });
    let running = 0;
    const curve = closed.flatMap((trade) => {
      if (trade.exitedAt == null || trade.pnl == null) return [];
      running += trade.pnl;
      return [{ date: trade.exitedAt.toISOString(), value: Math.round(running * 100) / 100 }];
    });
    const wins = closed.map((trade) => trade.pnl).filter((pnl): pnl is number => pnl != null && pnl > 0);
    const losses = closed.map((trade) => trade.pnl).filter((pnl): pnl is number => pnl != null && pnl < 0);
    const avgWin = wins.length ? wins.reduce((sum, pnl) => sum + pnl, 0) / wins.length : null;
    const avgLoss = losses.length ? Math.abs(losses.reduce((sum, pnl) => sum + pnl, 0) / losses.length) : null;
    const decided = wins.length + losses.length;
    const grossWin = wins.reduce((sum, pnl) => sum + pnl, 0);
    const grossLoss = Math.abs(losses.reduce((sum, pnl) => sum + pnl, 0));
    const expectancy = decided && avgWin != null
      ? ((wins.length / decided) * avgWin) - ((losses.length / decided) * (avgLoss || 0))
      : null;
    let peak = 0;
    let maxDrawdown = 0;
    running = 0;
    for (const trade of closed) {
      if (trade.pnl == null) continue;
      running += trade.pnl;
      peak = Math.max(peak, running);
      if (peak > 0) maxDrawdown = Math.max(maxDrawdown, (peak - running) / peak * 100);
    }
    const closedPnl = closed.reduce((sum, trade) => sum + (trade.pnl || 0), 0);

    return NextResponse.json({
      summary: {
        totalTrades: closed.length,
        winningTrades: wins.length,
        losingTrades: losses.length,
        winRate: closed.length ? (wins.length / closed.length) * 100 : 0,
        profitFactor: grossLoss > 0 ? grossWin / grossLoss : null,
        sharpeRatio: null,
        maxDrawdown: closed.length ? maxDrawdown : null,
        totalPnl: closedPnl,
        totalPnlPct: null,
        source: 'closed' as const,
        avgWin,
        avgLoss,
        expectancy,
        payoff: avgWin != null && avgLoss ? avgWin / avgLoss : null,
      },
      curve,
      daily: metrics.map(m => ({
        date: m.date.toISOString().split('T')[0],
        totalTrades: m.totalTrades,
        winningTrades: m.winningTrades,
        losingTrades: m.losingTrades,
        winRate: m.winRate,
        profitFactor: m.profitFactor,
        sharpeRatio: m.sharpeRatio,
        maxDrawdown: m.maxDrawdown,
        totalPnl: m.totalPnl,
        totalPnlPct: m.totalPnlPct,
      })),
    });
  } catch (error) {
    console.error('Get performance error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
