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
    const botName = searchParams.get('botName');

    const where: any = {};
    if (botName) {
      where.botName = botName;
    }

    const strategyPerformance = await prisma.strategyPerformance.findMany({
      where,
      orderBy: { totalPnl: 'desc' },
    });

    const openGroups = await prisma.position.groupBy({
      by: ['botName', 'strategy'],
      _count: { _all: true },
    });
    const heartbeats = await prisma.botStatus.findMany({
      select: { botName: true, lastHeartbeat: true },
    });
    const heartbeatByBot = new Map(heartbeats.map((row) => [row.botName, row.lastHeartbeat]));

    return NextResponse.json({
      strategies: strategyPerformance.map(sp => ({
        botName: sp.botName,
        strategyName: sp.strategyName,
        openPositions: openGroups.find((group) => group.botName === sp.botName && group.strategy === sp.strategyName)?._count._all ?? 0,
        status: (() => {
          const seen = heartbeatByBot.get(sp.botName);
          if (!seen) return 'stale';
          return Date.now() - seen.getTime() < 180_000 ? 'running' : 'stale';
        })(),
        totalTrades: sp.totalTrades,
        winningTrades: sp.winningTrades,
        losingTrades: sp.losingTrades,
        winRate: sp.winRate,
        totalPnl: sp.totalPnl,
        totalPnlPct: sp.totalPnlPct,
        avgWin: sp.avgWin,
        avgLoss: sp.avgLoss,
        largestWin: sp.largestWin,
        largestLoss: sp.largestLoss,
        sharpeRatio: sp.sharpeRatio,
        profitFactor: sp.profitFactor,
        maxDrawdown: sp.maxDrawdown,
        currentDrawdown: sp.currentDrawdown,
        lastTradeAt: sp.lastTradeAt?.toISOString(),
        updatedAt: sp.updatedAt.toISOString(),
      })),
    });
  } catch (error) {
    console.error('Get strategy performance error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
