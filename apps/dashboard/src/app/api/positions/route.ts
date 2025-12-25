import { NextResponse } from 'next/server';
import { getBotPositions } from '@/lib/redis';

// Disable caching for real-time data
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET() {
  try {
    const bots = ['equity-bot', 'crypto-bot'];
    const allPositions = [];

    for (const botName of bots) {
      try {
        const positions = await getBotPositions(botName);
        console.log(`Fetched positions for ${botName}:`, Object.keys(positions).length, 'positions');
        
        for (const [symbol, data] of Object.entries(positions)) {
          console.log(`Position ${symbol}:`, data);
          allPositions.push({
            bot: botName,
            symbol,
            ...data
          });
        }
      } catch (botError) {
        console.error(`Error fetching positions for ${botName}:`, botError);
      }
    }

    console.log('Total positions:', allPositions.length);
    return NextResponse.json({ positions: allPositions });
  } catch (error) {
    console.error('Error fetching positions:', error);
    return NextResponse.json(
      { error: 'Failed to fetch positions', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
