import { NextResponse } from 'next/server';
import { getBotPositions } from '@/lib/redis';

// Disable caching for real-time data
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const debug = searchParams.get('debug') === 'true';
  
  try {
    const bots = ['equity-bot', 'crypto-bot'];
    const allPositions = [];
    const debugInfo: any = { bots: {} };

    for (const botName of bots) {
      try {
        const positions = await getBotPositions(botName);
        debugInfo.bots[botName] = {
          positionCount: Object.keys(positions).length,
          symbols: Object.keys(positions)
        };
        
        for (const [symbol, data] of Object.entries(positions)) {
          allPositions.push({
            bot: botName,
            symbol,
            ...data
          });
        }
      } catch (botError) {
        debugInfo.bots[botName] = {
          error: botError instanceof Error ? botError.message : 'Unknown error'
        };
      }
    }

    if (debug) {
      return NextResponse.json({ 
        positions: allPositions,
        debug: debugInfo,
        totalPositions: allPositions.length
      });
    }

    return NextResponse.json({ positions: allPositions });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch positions', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
