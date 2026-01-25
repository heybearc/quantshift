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
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');
    const status = searchParams.get('status');
    const symbol = searchParams.get('symbol');

    const where: any = { botName: 'equity-bot' };
    if (status) where.status = status;
    if (symbol) where.symbol = symbol;

    const [trades, total] = await Promise.all([
      prisma.trade.findMany({
        where,
        orderBy: { enteredAt: 'desc' },
        take: limit,
        skip: offset,
      }),
      prisma.trade.count({ where }),
    ]);

    return NextResponse.json({
      trades: trades.map(trade => ({
        id: trade.id,
        symbol: trade.symbol,
        side: trade.side,
        quantity: trade.quantity,
        entryPrice: trade.entryPrice,
        exitPrice: trade.exitPrice,
        stopLoss: trade.stopLoss,
        takeProfit: trade.takeProfit,
        status: trade.status,
        pnl: trade.pnl,
        pnlPercent: trade.pnlPercent,
        strategy: trade.strategy,
        signalType: trade.signalType,
        entryReason: trade.entryReason,
        exitReason: trade.exitReason,
        enteredAt: trade.enteredAt.toISOString(),
        exitedAt: trade.exitedAt?.toISOString(),
      })),
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total,
      },
    });
  } catch (error) {
    console.error('Get trades error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
