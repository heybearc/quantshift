import { NextResponse } from 'next/server';
import { getBotPositions } from '@/lib/redis';

export async function GET() {
  try {
    const bots = ['equity-bot', 'crypto-bot'];
    const allPositions = [];

    for (const botName of bots) {
      const positions = await getBotPositions(botName);
      
      for (const [symbol, data] of Object.entries(positions)) {
        allPositions.push({
          bot: botName,
          symbol,
          ...data
        });
      }
    }

    return NextResponse.json({ positions: allPositions });
  } catch (error) {
    console.error('Error fetching positions:', error);
    return NextResponse.json(
      { error: 'Failed to fetch positions' },
      { status: 500 }
    );
  }
}
