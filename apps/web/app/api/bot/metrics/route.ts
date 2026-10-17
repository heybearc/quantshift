import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET() {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Same rows the Performance page strategy table uses.
    const strategyRows = await prisma.strategyPerformance.findMany();
    const botStatuses = await prisma.botStatus.findMany();
    const equityByBot = new Map(botStatuses.map((bot) => [bot.botName, bot.portfolioValue || 0]));

    const summarize = (rows: typeof strategyRows) => {
      const totalTrades = rows.reduce((sum, row) => sum + row.totalTrades, 0);
      const totalWins = rows.reduce((sum, row) => sum + row.winningTrades, 0);
      const totalLosses = rows.reduce((sum, row) => sum + row.losingTrades, 0);
      const winRate = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;
      const worstDrawdown = rows.reduce<(typeof rows)[number] | null>((worst, row) => {
        if (row.maxDrawdown == null) return worst;
        if (!worst || (worst.maxDrawdown ?? 0) < row.maxDrawdown) return row;
        return worst;
      }, null);
      const maxDrawdown = worstDrawdown?.maxDrawdown ?? null;
      const names = [...new Set(rows.map((row) => row.strategyName))];
      const stamps = rows
        .flatMap((row) => [row.createdAt, row.lastTradeAt, row.updatedAt])
        .filter((value): value is Date => value instanceof Date);
      const avgTradesPerDay = stamps.length > 0
        ? totalTrades / Math.max(1, Math.ceil((Math.max(...stamps.map((d) => d.getTime())) - Math.min(...stamps.map((d) => d.getTime()))) / 86400000))
        : 0;
      const lastTrade = rows
        .map((row) => row.lastTradeAt)
        .filter((value): value is Date => value instanceof Date)
        .sort((a, b) => b.getTime() - a.getTime())[0];
      const drawdownAmount = worstDrawdown?.maxDrawdown == null
        ? null
        : (equityByBot.get(worstDrawdown.botName) || 0) * (worstDrawdown.maxDrawdown / 100);

      return {
        winRate: Math.round(winRate * 100) / 100,
        totalWins,
        totalLosses,
        totalTrades,
        maxDrawdown: maxDrawdown == null ? null : Math.round(maxDrawdown * 100) / 100,
        maxDrawdownAmount: drawdownAmount == null ? null : Math.round(drawdownAmount * 100) / 100,
        avgTradesPerDay: Math.round(avgTradesPerDay * 100) / 100,
        lastTradeTime: lastTrade ? lastTrade.toISOString() : null,
        currentStrategy: names.length > 0 ? names.join(', ') : 'No recorded strategy',
        strategySuccessRate: Math.round(winRate * 100) / 100,
      };
    };

    const grouped = new Map<string, typeof strategyRows>();
    for (const row of strategyRows) {
      const list = grouped.get(row.botName) || [];
      list.push(row);
      grouped.set(row.botName, list);
    }
    const byBot: Record<string, ReturnType<typeof summarize>> = {};
    for (const [botName, rows] of grouped) {
      byBot[botName] = summarize(rows);
    }
    const overall = summarize(strategyRows);

    const openPositions = await prisma.position.groupBy({
      by: ['botName'],
      _sum: { unrealizedPl: true },
    });
    const openUnrealizedByBot: Record<string, number> = {};
    let openUnrealizedPl = 0;
    for (const row of openPositions) {
      const value = row._sum.unrealizedPl || 0;
      openUnrealizedByBot[row.botName] = value;
      openUnrealizedPl += value;
    }

    const closedByBot: Record<string, number> = {};
    for (const row of strategyRows) {
      closedByBot[row.botName] = (closedByBot[row.botName] || 0) + row.totalPnl;
    }
    const accountByBot = new Map(
      botStatuses.map((bot) => [bot.botName, bot.portfolioValue || bot.accountEquity || 0])
    );
    const paperStart: Record<string, number> = {
      'quantshift-crypto': 10000,
      'quantshift-kraken': 5000,
    };
    const bookNames = ['quantshift-equity', 'quantshift-crypto', 'quantshift-kraken'];
    const cents = (value: number) => Math.round(value * 100) / 100;
    const booksByBot: Record<string, {
      account: number;
      start: number | null;
      fromStart: number | null;
      closedPnl: number;
      openPnl: number;
      result: number;
    }> = {};
    for (const botName of bookNames) {
      const closedPnl = cents(closedByBot[botName] || 0);
      const openPnl = cents(openUnrealizedByBot[botName] || 0);
      const account = cents(accountByBot.get(botName) || 0);
      const start = paperStart[botName] ?? null;
      booksByBot[botName] = {
        account,
        start,
        fromStart: start == null ? null : cents(account - start),
        closedPnl,
        openPnl,
        result: cents(closedPnl + openPnl),
      };
    }
    const closedPnl = cents(bookNames.reduce((sum, name) => sum + booksByBot[name].closedPnl, 0));
    const openPnl = cents(bookNames.reduce((sum, name) => sum + booksByBot[name].openPnl, 0));

    return NextResponse.json({
      ...overall,
      openUnrealizedPl: cents(openUnrealizedPl),
      openUnrealizedByBot,
      byBot,
      books: {
        closedPnl,
        openPnl,
        result: cents(closedPnl + openPnl),
        byBot: booksByBot,
      },
    });
  } catch (error) {
    console.error('Error fetching bot metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch bot metrics' },
      { status: 500 }
    );
  }
}
