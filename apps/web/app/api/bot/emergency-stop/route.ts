import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

const REDIS_HOST = process.env.REDIS_HOST || '10.92.3.27';
const REDIS_PASSWORD = process.env.REDIS_PASSWORD || 'Cloudy_92!';

async function setRedisKey(key: string, value: string): Promise<void> {
  const cmd = `redis-cli -h ${REDIS_HOST} -a '${REDIS_PASSWORD}' SET ${key} ${value}`;
  await execAsync(cmd);
}

async function getRedisKey(key: string): Promise<string | null> {
  try {
    const cmd = `redis-cli -h ${REDIS_HOST} -a '${REDIS_PASSWORD}' GET ${key}`;
    const { stdout } = await execAsync(cmd);
    const result = stdout.trim();
    return result === '(nil)' ? null : result;
  } catch {
    return null;
  }
}

async function deleteRedisKey(key: string): Promise<void> {
  const cmd = `redis-cli -h ${REDIS_HOST} -a '${REDIS_PASSWORD}' DEL ${key}`;
  await execAsync(cmd);
}

export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    
    if (!user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    if (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN') {
      return NextResponse.json(
        { error: 'Forbidden - Admin access required' },
        { status: 403 }
      );
    }

    const body = await request.json();
    const { botName } = body;

    if (!botName) {
      return NextResponse.json(
        { error: 'Bot name is required' },
        { status: 400 }
      );
    }

    const validBots = ['quantshift-equity', 'quantshift-crypto'];
    if (!validBots.includes(botName)) {
      return NextResponse.json(
        { error: `Invalid bot name. Must be one of: ${validBots.join(', ')}` },
        { status: 400 }
      );
    }

    const emergencyKey = `bot:${botName}:emergency_stop`;
    await setRedisKey(emergencyKey, 'true');

    console.log(`Emergency stop triggered for ${botName} by user ${user.id}`);

    return NextResponse.json({
      success: true,
      message: `Emergency stop triggered for ${botName}`,
      botName,
      triggeredBy: user.id,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Emergency stop API error:', error);
    return NextResponse.json(
      { error: 'Failed to trigger emergency stop' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const user = await getCurrentUser();
    
    if (!user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    if (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN') {
      return NextResponse.json(
        { error: 'Forbidden - Admin access required' },
        { status: 403 }
      );
    }

    const equityKey = 'bot:quantshift-equity:emergency_stop';
    const cryptoKey = 'bot:quantshift-crypto:emergency_stop';

    const [equityStatus, cryptoStatus] = await Promise.all([
      getRedisKey(equityKey),
      getRedisKey(cryptoKey),
    ]);

    return NextResponse.json({
      equity: equityStatus === 'true',
      crypto: cryptoStatus === 'true',
    });

  } catch (error) {
    console.error('Emergency stop status check error:', error);
    return NextResponse.json(
      { error: 'Failed to check emergency stop status' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const user = await getCurrentUser();
    
    if (!user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    if (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN') {
      return NextResponse.json(
        { error: 'Forbidden - Admin access required' },
        { status: 403 }
      );
    }

    const body = await request.json();
    const { botName } = body;

    if (!botName) {
      return NextResponse.json(
        { error: 'Bot name is required' },
        { status: 400 }
      );
    }

    const emergencyKey = `bot:${botName}:emergency_stop`;
    await deleteRedisKey(emergencyKey);

    console.log(`Emergency stop cleared for ${botName} by user ${user.id}`);

    return NextResponse.json({
      success: true,
      message: `Emergency stop cleared for ${botName}`,
      botName,
      clearedBy: user.id,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Emergency stop clear error:', error);
    return NextResponse.json(
      { error: 'Failed to clear emergency stop' },
      { status: 500 }
    );
  }
}
