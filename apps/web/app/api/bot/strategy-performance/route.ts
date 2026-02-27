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

    return NextResponse.json({
      strategies: strategyPerformance.map(sp => ({
        botName: sp.botName,
        strategyName: sp.strategyName,
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
