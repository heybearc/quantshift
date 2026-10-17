import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the snap cooldown.
 * A stop is recorded on the crypto books. The same side then waits
 * for price to close back through the middle. That wait lives in the bot.
 */

const REASONS = new Set([
  'band snap long',
  'band snap short',
  'paper stop',
  'paper take profit',
  'band snap time stop',
]);

test('snap stops stay on the crypto books', async ({ page }) => {
  await login(page);
  const response = await page.request.get('/api/bot/trades?limit=200');
  expect(response.status()).toBe(200);
  const trades = (await response.json()).trades as Array<{
    botName: string;
    strategy: string;
    entryReason: string | null;
  }>;
  const snaps = trades.filter((trade) => trade.strategy === 'BandSnapSetup');
  expect(snaps.length).toBeGreaterThan(0);
  for (const trade of snaps) {
    const book = trade.botName.toLowerCase();
    expect(book.includes('crypto') || book.includes('kraken')).toBe(true);
    expect(book.includes('equity')).toBe(false);
    expect(REASONS.has(trade.entryReason || '')).toBe(true);
  }
  expect(snaps.some((trade) => trade.entryReason === 'paper stop')).toBe(true);
});
