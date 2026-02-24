import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get latest bot status
    const botStatus = await prisma.botStatus.findFirst({
      where: { botName: 'quantshift-equity' },
      orderBy: { updatedAt: 'desc' },
    });

    if (!botStatus) {
      return NextResponse.json({
        status: 'UNKNOWN',
        message: 'Bot status not available',
      });
    }

    // Check if bot is stale (no heartbeat in last 5 minutes)
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    const isStale = botStatus.lastHeartbeat < fiveMinutesAgo;

    return NextResponse.json({
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
    });
  } catch (error) {
    console.error('Get bot status error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
