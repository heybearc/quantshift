const { createClient } = require('redis');

async function testRedis() {
  const client = createClient({
    url: 'redis://:Cloudy_92!@10.92.3.27:6379/0'
  });

  try {
    await client.connect();
    console.log('✅ Connected to Redis');

    // Test getting bot state
    const state = await client.get('bot:equity-bot:state');
    console.log('Bot state:', state ? JSON.parse(state) : null);

    // Test getting positions
    const keys = [];
    for await (const key of client.scanIterator({ MATCH: 'bot:equity-bot:position:*' })) {
      keys.push(key);
    }
    console.log('Position keys found:', keys);

    for (const key of keys) {
      const data = await client.get(key);
      console.log(`${key}:`, JSON.parse(data));
    }

    await client.quit();
  } catch (error) {
    console.error('❌ Redis error:', error);
  }
}

testRedis();
