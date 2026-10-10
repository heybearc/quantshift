import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

function botLabel(botName: string): string {
  if (botName.includes('equity')) return 'equity';
  if (botName.includes('crypto')) return 'crypto';
  if (botName.includes('kraken')) return 'kraken';
  return botName;
}

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const botName = new URL(request.url).searchParams.get('botName');
    const rows = await prisma.strategyPerformance.findMany({
      where: botName ? { botName } : {},
      orderBy: [{ botName: 'asc' }, { strategyName: 'asc' }],
    });

    return NextResponse.json(rows.map((row) => {
      const winRate = row.winRate > 1 ? row.winRate / 100 : row.winRate;
      return {
        strategy_name: `${row.strategyName} · ${botLabel(row.botName)}`,
        enabled: true,
        performance_metrics: {
          win_rate: winRate,
          sharpe: row.sharpeRatio,
          trades: row.totalTrades,
        },
      };
    }));
  } catch (error) {
    console.error('Error fetching strategy status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch strategy status' },
      { status: 500 }
    );
  }
}
