import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET() {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get all closed trades to calculate metrics
    const closedTrades = await prisma.trade.findMany({
      where: {
        status: 'CLOSED',
        exitedAt: { not: null },
        pnl: { not: null }
      },
      orderBy: {
        exitedAt: 'desc'
      }
    });

    // Calculate win rate
    const totalTrades = closedTrades.length;
    const winningTrades = closedTrades.filter(t => (t.pnl || 0) > 0).length;
    const losingTrades = closedTrades.filter(t => (t.pnl || 0) < 0).length;
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;

    // Calculate max drawdown from equity history
    // Get bot status for current equity
    const botStatus = await prisma.botStatus.findFirst({
      orderBy: { updatedAt: 'desc' }
    });

    // For max drawdown, we'll use performance metrics if available
    const latestPerformance = await prisma.performanceMetrics.findFirst({
      orderBy: { date: 'desc' }
    });

    const maxDrawdown = latestPerformance?.maxDrawdown || 0;
    const maxDrawdownAmount = botStatus?.accountEquity 
      ? (botStatus.accountEquity * (maxDrawdown / 100))
      : 0;

    // Calculate average trades per day
    if (closedTrades.length > 0) {
      const firstTrade = closedTrades[closedTrades.length - 1];
      const lastTrade = closedTrades[0];
      const daysDiff = Math.max(
        1,
        Math.ceil(
          (new Date(lastTrade.exitedAt!).getTime() - 
           new Date(firstTrade.exitedAt!).getTime()) / 
          (1000 * 60 * 60 * 24)
        )
      );
      var avgTradesPerDay = totalTrades / daysDiff;
    } else {
      var avgTradesPerDay = 0;
    }

    // Get last trade time
    const lastTrade = closedTrades[0];
    const lastTradeTime = lastTrade?.exitedAt || null;

    // Get current strategy from bot config
    const botConfig = await prisma.botConfig.findFirst({
      where: { enabled: true }
    });

    const currentStrategy = botConfig?.strategy || 'Unknown';
    
    // Calculate strategy success rate (same as win rate for now)
    const strategySuccessRate = winRate;

    const openPositions = await prisma.position.groupBy({
      by: ['botName'],
      where: { quantity: { gt: 0 } },
      _sum: { unrealizedPl: true },
    });
    const openUnrealizedByBot: Record<string, number> = {};
    let openUnrealizedPl = 0;
    for (const row of openPositions) {
      const value = row._sum.unrealizedPl || 0;
      openUnrealizedByBot[row.botName] = value;
      openUnrealizedPl += value;
    }

    return NextResponse.json({
      winRate: Math.round(winRate * 100) / 100,
      totalWins: winningTrades,
      totalLosses: losingTrades,
      totalTrades,
      maxDrawdown: Math.round(maxDrawdown * 100) / 100,
      maxDrawdownAmount: Math.round(maxDrawdownAmount * 100) / 100,
      avgTradesPerDay: Math.round(avgTradesPerDay * 100) / 100,
      lastTradeTime,
      currentStrategy,
      strategySuccessRate: Math.round(strategySuccessRate * 100) / 100,
      openUnrealizedPl: Math.round(openUnrealizedPl * 100) / 100,
      openUnrealizedByBot,
    });
  } catch (error) {
    console.error('Error fetching bot metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch bot metrics' },
      { status: 500 }
    );
  }
}
