import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';
import { getBotPositions } from '@/lib/redis';

const prisma = new PrismaClient();

export async function GET() {
  try {
    // Get positions from Redis
    const equityPositions = await getBotPositions('equity-bot');
    const cryptoPositions = await getBotPositions('crypto-bot');
    
    const totalPositions = Object.keys(equityPositions).length + Object.keys(cryptoPositions).length;
    
    // Calculate unrealized P&L
    let unrealizedPnl = 0;
    for (const pos of Object.values(equityPositions)) {
      if (pos.quantity && pos.entry_price && pos.current_price) {
        unrealizedPnl += (pos.current_price - pos.entry_price) * pos.quantity;
      }
    }
    for (const pos of Object.values(cryptoPositions)) {
      if (pos.quantity && pos.entry_price && pos.current_price) {
        unrealizedPnl += (pos.current_price - pos.entry_price) * pos.quantity;
      }
    }

    // Get trade statistics from database
    const trades = await prisma.trade.findMany({
      where: {
        timestamp: {
          gte: new Date(new Date().setHours(0, 0, 0, 0)) // Today
        }
      }
    });

    const todayTrades = trades.length;
    const closedTrades = trades.filter((t: any) => t.action === 'SELL');
    const winningTrades = closedTrades.filter((t: any) => (t.pnl || 0) > 0);
    const winRate = closedTrades.length > 0 
      ? (winningTrades.length / closedTrades.length) * 100 
      : 0;

    // Get total realized P&L
    const realizedPnl = closedTrades.reduce((sum: number, t: any) => sum + (t.pnl || 0), 0);

    return NextResponse.json({
      totalPositions,
      unrealizedPnl,
      todayTrades,
      winRate,
      realizedPnl,
      accountBalance: 10000.00 // TODO: Get from actual account
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      { error: 'Failed to fetch stats', details: errorMessage },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}
