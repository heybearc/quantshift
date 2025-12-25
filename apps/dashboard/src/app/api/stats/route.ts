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
    const closedTrades = trades.filter((t: any) => t.side === 'SELL');
    
    // Calculate P&L from trades (simplified - actual P&L calculation would need matching buy/sell pairs)
    const winningTrades = closedTrades.length; // Placeholder
    const winRate = 0; // TODO: Implement proper win rate calculation
    const realizedPnl = 0; // TODO: Implement proper P&L calculation

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
