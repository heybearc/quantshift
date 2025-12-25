import { NextResponse } from 'next/server';
import { getBotState, getBotHeartbeat, getBotPositions } from '@/lib/redis';

export async function GET() {
  try {
    const bots = ['equity-bot', 'crypto-bot'];
    const botData = [];

    for (const botName of bots) {
      try {
        const state = await getBotState(botName);
        const heartbeat = await getBotHeartbeat(botName);
        const positions = await getBotPositions(botName);

        console.log(`Bot ${botName} - State:`, state);
        console.log(`Bot ${botName} - Heartbeat:`, heartbeat);
        console.log(`Bot ${botName} - Positions:`, Object.keys(positions).length);

        const isAlive = heartbeat ? 
          (new Date().getTime() - new Date(heartbeat).getTime()) < 120000 : // 2 minutes
          false;

        botData.push({
          name: botName,
          status: isAlive ? 'running' : 'stopped',
          state: state || {},
          heartbeat: heartbeat,
          positions: Object.keys(positions).length,
          lastUpdate: state?.last_update || null
        });
      } catch (botError) {
        console.error(`Error fetching data for ${botName}:`, botError);
        botData.push({
          name: botName,
          status: 'error',
          state: {},
          heartbeat: null,
          positions: 0,
          lastUpdate: null
        });
      }
    }

    return NextResponse.json({ bots: botData });
  } catch (error) {
    console.error('Error fetching bot data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch bot data', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
