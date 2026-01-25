const { createClient } = require("redis");

async function test() {
  console.log("Creating Redis client...");
  const client = createClient({
    url: "redis://:Cloudy_92!@10.92.3.27:6379/0"
  });

  client.on("error", (err) => console.error("Redis Error:", err));
  client.on("connect", () => console.log("Connected!"));

  try {
    console.log("Connecting...");
    await client.connect();
    
    console.log("Getting bot state...");
    const state = await client.get("bot:equity-bot:state");
    console.log("State:", state);

    console.log("Scanning for positions...");
    const positions = {};
    for await (const key of client.scanIterator({ MATCH: "bot:equity-bot:position:*" })) {
      console.log("Found key:", key);
      const data = await client.get(key);
      positions[key] = JSON.parse(data);
    }
    console.log("Positions:", positions);

    await client.quit();
  } catch (error) {
    console.error("Error:", error);
  }
}

test();
