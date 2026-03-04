import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const botName = searchParams.get('bot') || 'quantshift-equity';

    // In a real implementation, this would send a command to the bot
    // For now, we'll update Redis to signal the bot to reset
    try {
      const redis = require('redis');
      const client = redis.createClient({
        url: process.env.REDIS_URL || 'redis://10.92.3.21:6379'
      });
      
      await client.connect();
      
      // Set a flag for the bot to reset circuit breaker
      await client.set(`bot:${botName}:reset_circuit_breaker`, 'true', {
        EX: 60 // Expire after 60 seconds
      });
      
      await client.quit();
      
      return NextResponse.json({ 
        success: true,
        message: 'Circuit breaker reset signal sent to bot'
      });
    } catch (redisError) {
      console.error('Redis error:', redisError);
      return NextResponse.json(
        { error: 'Failed to communicate with bot' },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Error resetting circuit breaker:', error);
    return NextResponse.json(
      { error: 'Failed to reset circuit breaker' },
      { status: 500 }
    );
  }
}
