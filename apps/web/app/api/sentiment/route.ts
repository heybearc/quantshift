import { NextRequest, NextResponse } from 'next/server';
import { createClient } from 'redis';

/**
 * GET /api/sentiment
 * 
 * Get current sentiment scores for all active symbols
 * Returns sentiment data from bot's in-memory cache via Redis
 */
export async function GET(request: NextRequest) {
  try {
    // TODO: Add authentication when needed
    // For now, this is internal-only and behind the dashboard auth

    // Connect to Redis
    const redisClient = createClient({
      socket: {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT || '6379'),
      },
    });

    await redisClient.connect();

    try {
      // Get all sentiment keys
      const keys = await redisClient.keys('sentiment:*');
      
      const sentiment: Record<string, any> = {};
      
      // Fetch each sentiment value
      for (const key of keys) {
        const symbol = key.replace('sentiment:', '');
        const data = await redisClient.get(key);
        
        if (data) {
          try {
            sentiment[symbol] = JSON.parse(data);
          } catch (e) {
            console.error(`Failed to parse sentiment for ${symbol}:`, e);
          }
        }
      }

      await redisClient.quit();

      // If no sentiment data in Redis, return empty object
      if (Object.keys(sentiment).length === 0) {
        return NextResponse.json({ 
          sentiment: {},
          message: 'No sentiment data available yet. Bots will populate data as they analyze news.'
        });
      }

      return NextResponse.json({ sentiment });
    } catch (error) {
      await redisClient.quit();
      throw error;
    }
  } catch (error) {
    console.error('Sentiment API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch sentiment data' },
      { status: 500 }
    );
  }
}
