import { NextResponse } from 'next/server';
import { getBotState, getBotHeartbeat, getBotPositions } from '@/lib/redis';

export async function GET() {
  try {
    const bots = ['equity-bot', 'crypto-bot'];
    const botData = [];

    for (const botName of bots) {
      const state = await getBotState(botName);
      const heartbeat = await getBotHeartbeat(botName);
      const positions = await getBotPositions(botName);

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
    }

    return NextResponse.json({ bots: botData });
  } catch (error) {
    console.error('Error fetching bot data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch bot data' },
      { status: 500 }
    );
  }
}
