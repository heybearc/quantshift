import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

function accountDrawdown(pnls: number[], startingCapital: number): number {
  if (startingCapital <= 0) return 0;
  let cumulative = 0;
  let peak = 0;
  let worst = 0;
  for (const pnl of pnls) {
    cumulative += pnl;
    if (cumulative > peak) peak = cumulative;
    const peakEquity = startingCapital + peak;
    const equity = startingCapital + cumulative;
    if (peakEquity <= 0 || equity >= peakEquity) continue;
    const decline = ((peakEquity - equity) / peakEquity) * 100;
    if (decline > worst) worst = decline;
  }
  return worst;
}

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
      select: { botName: true, exitedAt: true, pnl: true },
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
    const statuses = await prisma.botStatus.findMany();
    const pnlByBot = new Map<string, number[]>();
    for (const trade of closed) {
      if (trade.pnl == null) continue;
      const list = pnlByBot.get(trade.botName) ?? [];
      list.push(trade.pnl);
      pnlByBot.set(trade.botName, list);
    }
    let maxDrawdown = 0;
    for (const [name, pnls] of pnlByBot) {
      const status = statuses.find((row) => row.botName === name);
      const closedPnl = pnls.reduce((sum, pnl) => sum + pnl, 0);
      const equity = status?.accountEquity ?? 0;
      const unrealized = status?.unrealizedPl ?? 0;
      const starting = equity - unrealized - closedPnl;
      maxDrawdown = Math.max(maxDrawdown, accountDrawdown(pnls, starting > 0 ? starting : equity));
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
