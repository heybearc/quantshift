import { NextResponse } from 'next/server';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');
    const bot = searchParams.get('bot');

    const where = bot ? { bot_name: bot } : {};

    const trades = await prisma.trade.findMany({
      where,
      orderBy: { timestamp: 'desc' },
      take: limit
    });

    return NextResponse.json({ trades });
  } catch (error) {
    console.error('Error fetching trades:', error);
    return NextResponse.json(
      { error: 'Failed to fetch trades' },
      { status: 500 }
    );
  } finally {
    await prisma.$disconnect();
  }
}
