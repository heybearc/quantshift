import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

const BOT_NAMES = ['quantshift-equity', 'quantshift-crypto'];
const STALE_THRESHOLD_MS = 5 * 60 * 1000;

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const results = await Promise.all(
      BOT_NAMES.map(async (botName) => {
        const botStatus = await prisma.botStatus.findFirst({
          where: { botName },
          orderBy: { updatedAt: 'desc' },
        });

        if (!botStatus) {
          return {
            botName,
            status: 'UNKNOWN',
            lastHeartbeat: null,
            accountEquity: 0,
            accountCash: 0,
            buyingPower: 0,
            portfolioValue: 0,
            unrealizedPl: 0,
            realizedPl: 0,
            positionsCount: 0,
            tradesCount: 0,
            errorMessage: null,
            updatedAt: null,
          };
        }

        const isStale = botStatus.lastHeartbeat < new Date(Date.now() - STALE_THRESHOLD_MS);

        return {
          botName,
          status: isStale ? 'STALE' : botStatus.status,
          lastHeartbeat: botStatus.lastHeartbeat.toISOString(),
          accountEquity: botStatus.accountEquity,
          accountCash: botStatus.accountCash,
          buyingPower: botStatus.buyingPower,
          portfolioValue: botStatus.portfolioValue,
          unrealizedPl: botStatus.unrealizedPl,
          realizedPl: botStatus.realizedPl,
          positionsCount: botStatus.positionsCount,
          tradesCount: botStatus.tradesCount,
          errorMessage: botStatus.errorMessage,
          updatedAt: botStatus.updatedAt.toISOString(),
        };
      })
    );

    return NextResponse.json({ bots: results });
  } catch (error) {
    console.error('Get all bot status error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
