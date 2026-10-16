import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the 15-minute band snap on crypto and Kraken.
 * Those books may name BandSnapSetup. Equity does not.
 */

const SNAP = 'BandSnapSetup';

const CRYPTO_STRATEGIES = [
  'BollingerBounce',
  'RSIMeanReversion',
  'KeltnerChannelStrategy',
  'VWAPReversionStrategy',
  'BreakoutMomentum',
  'MACrossoverStrategy',
  'DonchianBreakoutStrategy',
  'StrategyOrchestrator',
  'TradeConfidentSetup',
  'VolatilityBreakoutSetup',
  SNAP,
];

test.describe('Band snap on crypto and Kraken', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('equity does not use the band snap', async ({ page }) => {
    const response = await page.request.get('/api/bot/strategy-performance');
    expect(response.status()).toBe(200);
    const rows = (await response.json()).strategies as Array<{ botName: string; strategyName: string }>;

    const equity = rows.filter((row) => row.botName.toLowerCase().includes('equity'));
    const crypto = rows.filter((row) => row.botName.toLowerCase().includes('crypto'));
    const kraken = rows.filter((row) => row.botName.toLowerCase().includes('kraken'));

    expect(equity.length).toBeGreaterThan(0);
    expect(crypto.length).toBeGreaterThan(0);
    for (const row of equity) {
      expect(row.strategyName).not.toBe(SNAP);
    }
    for (const row of [...crypto, ...kraken]) {
      expect(CRYPTO_STRATEGIES).toContain(row.strategyName);
    }

    const positions = await page.request.get('/api/bot/positions');
    expect(positions.status()).toBe(200);
    const open = (await positions.json()).positions as Array<{ botName: string; strategy: string }>;
    for (const position of open) {
      if (position.strategy !== SNAP) continue;
      const book = position.botName.toLowerCase();
      expect(book.includes('crypto') || book.includes('kraken')).toBe(true);
      expect(book.includes('equity')).toBe(false);
    }

    await page.goto('/performance');
    await expect(page.getByText(crypto[0].strategyName).first()).toBeVisible();
  });
});
