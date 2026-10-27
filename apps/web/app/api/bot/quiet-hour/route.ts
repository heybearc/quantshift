import { NextResponse } from 'next/server';
import { createClient } from 'redis';
import { getCurrentUser } from '@/lib/auth';

const BOOKS = ['quantshift-crypto', 'quantshift-kraken'];

export async function GET() {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const redisHost = process.env.REDIS_HOST || 'localhost';
  const redisPort = parseInt(process.env.REDIS_PORT || '6379');
  const redisPassword = process.env.REDIS_PASSWORD;
  const redisClient = createClient({
    socket: { host: redisHost, port: redisPort },
    password: redisPassword,
  });

  try {
    await redisClient.connect();
    const books = [];
    for (const botName of BOOKS) {
      const raw = await redisClient.get(`quiet-hour:${botName}`);
      if (!raw) continue;
      const report = JSON.parse(raw);
      books.push({
        botName,
        checked: report.checked || 0,
        unfinished: report.unfinished || 0,
        noSqueeze: report.no_squeeze || 0,
        noPivot: report.no_pivot || 0,
        alreadyOpen: report.already_open || 0,
        passed: report.passed || 0,
        updated: report.updated || null,
        examples: Array.isArray(report.examples) ? report.examples.slice(0, 4) : [],
      });
    }
    await redisClient.quit();
    return NextResponse.json({ books });
  } catch (error) {
    try {
      await redisClient.quit();
    } catch {
      // The client may never have connected.
    }
    console.error('quiet hour read failed', error);
    return NextResponse.json({ books: [] });
  }
}
