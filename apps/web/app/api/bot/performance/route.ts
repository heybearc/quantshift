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

    const strategyWhere: { botName?: string } = {};
    if (botName) strategyWhere.botName = botName;
    const strategies = await prisma.strategyPerformance.findMany({ where: strategyWhere });

    // Calculate aggregate metrics
    const totalTrades = metrics.reduce((sum, m) => sum + m.totalTrades, 0);
    const totalWins = metrics.reduce((sum, m) => sum + m.winningTrades, 0);
    const totalLosses = metrics.reduce((sum, m) => sum + m.losingTrades, 0);
    const totalPnl = metrics.reduce((sum, m) => sum + m.totalPnl, 0);

    const avgWinRate = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;
    const avgProfitFactor = metrics.length > 0
      ? metrics.reduce((sum, m) => sum + (m.profitFactor || 0), 0) / metrics.length
      : 0;
    const avgSharpe = metrics.length > 0
      ? metrics.reduce((sum, m) => sum + (m.sharpeRatio || 0), 0) / metrics.length
      : 0;
    const maxDrawdown = metrics.length > 0 ? Math.min(...metrics.map(m => m.maxDrawdown || 0)) : 0;

    const strategyTrades = strategies.reduce((sum, row) => sum + row.totalTrades, 0);
    const strategyWins = strategies.reduce((sum, row) => sum + row.winningTrades, 0);
    const strategyLosses = strategies.reduce((sum, row) => sum + row.losingTrades, 0);
    const strategyPnl = strategies.reduce((sum, row) => sum + row.totalPnl, 0);
    const recordedDrawdowns = strategies
      .map((row) => row.maxDrawdown)
      .filter((value): value is number => value != null);
    const recordedSharpes = strategies
      .map((row) => row.sharpeRatio)
      .filter((value): value is number => value != null);
    const recordedFactors = strategies
      .map((row) => row.profitFactor)
      .filter((value): value is number => value != null);

    const summary = strategyTrades > 0
      ? {
          totalTrades: strategyTrades,
          winningTrades: strategyWins,
          losingTrades: strategyLosses,
          winRate: (strategyWins / strategyTrades) * 100,
          profitFactor: recordedFactors.length > 0
            ? recordedFactors.reduce((sum, value) => sum + value, 0) / recordedFactors.length
            : null,
          sharpeRatio: recordedSharpes.length > 0
            ? recordedSharpes.reduce((sum, value) => sum + value, 0) / recordedSharpes.length
            : null,
          maxDrawdown: recordedDrawdowns.length > 0 ? Math.max(...recordedDrawdowns) : null,
          totalPnl: strategyPnl,
          totalPnlPct: null,
          source: 'strategy' as const,
        }
      : {
          totalTrades,
          winningTrades: totalWins,
          losingTrades: totalLosses,
          winRate: avgWinRate,
          profitFactor: avgProfitFactor,
          sharpeRatio: avgSharpe,
          maxDrawdown,
          totalPnl,
          totalPnlPct: metrics.length > 0 ? metrics[metrics.length - 1].totalPnlPct : 0,
          source: 'daily' as const,
        };

    return NextResponse.json({
      summary,
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
