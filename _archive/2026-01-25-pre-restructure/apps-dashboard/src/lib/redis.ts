import { createClient, RedisClientType } from 'redis';

let redisClient: RedisClientType | null = null;

async function getRedisClient() {
  if (!redisClient) {
    redisClient = createClient({
      url: process.env.REDIS_URL || 'redis://:Cloudy_92!@10.92.3.27:6379/0',
      socket: {
        reconnectStrategy: (retries) => Math.min(retries * 50, 500),
        connectTimeout: 10000
      }
    });

    redisClient.on('error', (err) => {
      console.error('Redis Client Error:', err);
    });

    redisClient.on('connect', () => {
      console.log('Redis client connected');
    });

    await redisClient.connect();
  }

  return redisClient;
}

export async function getBotState(botName: string) {
  const client = await getRedisClient();
  const key = `bot:${botName}:state`;
  const data = await client.get(key);
  return data ? JSON.parse(data) : null;
}

export async function getBotPositions(botName: string) {
  try {
    const client = await getRedisClient();
    const pattern = `bot:${botName}:position:*`;
    
    const positions: Record<string, any> = {};
    
    // Use KEYS command for now (works better in some Redis client versions)
    // Note: SCAN is preferred for production but KEYS works for small datasets
    const keys = await client.keys(pattern);
    
    for (const key of keys) {
      const parts = key.split(':');
      const symbol = parts[parts.length - 1];
      if (symbol) {
        const data = await client.get(key);
        if (data) {
          try {
            positions[symbol] = JSON.parse(data);
          } catch (parseError) {
            console.error(`[Redis] Failed to parse position data for ${symbol}:`, parseError);
          }
        }
      }
    }
    
    return positions;
  } catch (error) {
    console.error(`[Redis] Error in getBotPositions for ${botName}:`, error);
    throw error; // Re-throw to see the actual error
  }
}

export async function getBotHeartbeat(botName: string) {
  const client = await getRedisClient();
  const key = `bot:${botName}:heartbeat`;
  const data = await client.get(key);
  return data;
}

export async function getAllBotKeys() {
  const client = await getRedisClient();
  const keys = [];
  
  for await (const key of client.scanIterator({ MATCH: 'bot:*' })) {
    keys.push(key);
  }
  
  return keys;
}
