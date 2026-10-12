import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    
    if (!user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const botStatuses = await prisma.botStatus.findMany({
      orderBy: { botName: 'asc' },
    });

    const bots = await Promise.all(botStatuses.map(async (bot) => {
      const lastHeartbeat = bot.lastHeartbeat;
      const heartbeatAgeSeconds = lastHeartbeat
        ? Math.max(0, Math.floor((Date.now() - lastHeartbeat.getTime()) / 1000))
        : null;

      const strategyRows = await prisma.$queryRaw<{ count: number }[]>`
        SELECT COUNT(DISTINCT strategy)::int AS count
        FROM trades
        WHERE bot_name = ${bot.botName}
          AND created_at > NOW() - INTERVAL '7 days'
          AND strategy IS NOT NULL
          AND strategy <> ''
      `;
      const activeStrategies = Number(strategyRows[0]?.count ?? 0);

      const regimeRows = await prisma.$queryRaw<{ regime: string | null }[]>`
        SELECT regime FROM regime_history
        WHERE bot_name = ${bot.botName}
        ORDER BY timestamp DESC
        LIMIT 1
      `;
      const currentRegime = (regimeRows[0]?.regime || 'UNKNOWN').toString().trim().toUpperCase();

      return {
        botName: bot.botName,
        lastHeartbeat: lastHeartbeat?.toISOString() ?? null,
        heartbeatAgeSeconds,
        errors24h: bot.errorMessage ? 1 : 0,
        currentRegime,
        activeStrategies,
        unrealizedPl: bot.unrealizedPl,
        openPositions: bot.positionsCount,
        status: heartbeatAgeSeconds != null && heartbeatAgeSeconds < 180 ? 'running' : 'stale',
      };
    }));

    return NextResponse.json({
      bots,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Bot health API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch bot health' },
      { status: 500 }
    );
  }
}
