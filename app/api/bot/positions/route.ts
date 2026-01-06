import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { prisma } from '@/lib/prisma';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const positions = await prisma.position.findMany({
      where: { botName: 'equity-bot' },
      orderBy: { enteredAt: 'desc' },
    });

    return NextResponse.json({
      positions: positions.map(position => ({
        id: position.id,
        symbol: position.symbol,
        quantity: position.quantity,
        entryPrice: position.entryPrice,
        currentPrice: position.currentPrice,
        marketValue: position.marketValue,
        costBasis: position.costBasis,
        unrealizedPl: position.unrealizedPl,
        unrealizedPlPct: position.unrealizedPlPct,
        stopLoss: position.stopLoss,
        takeProfit: position.takeProfit,
        strategy: position.strategy,
        enteredAt: position.enteredAt.toISOString(),
      })),
    });
  } catch (error) {
    console.error('Get positions error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
