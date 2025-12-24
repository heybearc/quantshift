import { createClient } from 'redis';

const redisClient = createClient({
  url: process.env.REDIS_URL || 'redis://:Cloudy_92!@10.92.3.27:6379/0',
  socket: {
    reconnectStrategy: (retries) => Math.min(retries * 50, 500)
  }
});

redisClient.on('error', (err) => console.error('Redis Client Error', err));

let isConnected = false;

export async function getRedisClient() {
  if (!isConnected) {
    await redisClient.connect();
    isConnected = true;
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
  const client = await getRedisClient();
  const pattern = `bot:${botName}:position:*`;
  
  const positions: Record<string, any> = {};
  
  for await (const keyStr of client.scanIterator({ MATCH: pattern })) {
    const key = String(keyStr);
    const parts = key.split(':');
    const symbol = parts[parts.length - 1];
    if (symbol) {
      const data = await client.get(key);
      if (data) {
        positions[symbol] = JSON.parse(data);
      }
    }
  }
  
  return positions;
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
