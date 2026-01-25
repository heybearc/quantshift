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

    const metrics = await prisma.performanceMetrics.findMany({
      where: {
        botName: 'equity-bot',
        date: { gte: startDate },
      },
      orderBy: { date: 'asc' },
    });

    // If no performance metrics exist yet, return empty data
    if (metrics.length === 0) {
      return NextResponse.json({
        summary: {
          totalTrades: 0,
          winningTrades: 0,
          losingTrades: 0,
          winRate: 0,
          profitFactor: 0,
          sharpeRatio: 0,
          maxDrawdown: 0,
          totalPnl: 0,
          totalPnlPct: 0,
        },
        daily: [],
      });
    }

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

    return NextResponse.json({
      summary: {
        totalTrades,
        winningTrades: totalWins,
        losingTrades: totalLosses,
        winRate: avgWinRate,
        profitFactor: avgProfitFactor,
        sharpeRatio: avgSharpe,
        maxDrawdown,
        totalPnl,
        totalPnlPct: metrics.length > 0 ? metrics[metrics.length - 1].totalPnlPct : 0,
      },
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
