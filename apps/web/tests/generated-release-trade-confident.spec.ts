import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the zone setup.
 * Equity, Coinbase, and Kraken may name the washout. Equity stays long only.
 */

const EARLIER = [
  'BollingerBounce',
  'RSIMeanReversion',
  'KeltnerChannelStrategy',
  'VWAPReversionStrategy',
  'BreakoutMomentum',
  'MACrossoverStrategy',
  'DonchianBreakoutStrategy',
  'StrategyOrchestrator',
  'Unknown',
];

const ZONE = 'TradeConfidentSetup';
const BREAKOUT = 'VolatilityBreakoutSetup';

test.describe('Crypto and Kraken zone setup', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('equity may use the washout and the volatility break', async ({ page }) => {
    const response = await page.request.get('/api/bot/strategy-performance');
    expect(response.status()).toBe(200);
    const rows = (await response.json()).strategies as Array<{ botName: string; strategyName: string }>;

    const equity = rows.filter((row) => row.botName.toLowerCase().includes('equity'));
    const crypto = rows.filter((row) => row.botName.toLowerCase().includes('crypto'));
    const kraken = rows.filter((row) => row.botName.toLowerCase().includes('kraken'));

    for (const row of equity) {
      expect([...EARLIER, ZONE, BREAKOUT]).toContain(row.strategyName);
      expect(row.strategyName).not.toBe('BandSnapSetup');
      expect(row.strategyName).not.toBe('SprintBreakSetup');
    }
    for (const row of [...crypto, ...kraken]) {
      expect([...EARLIER, ZONE, BREAKOUT, 'BandSnapSetup', 'SprintBreakSetup']).toContain(row.strategyName);
    }

    if (equity[0] && crypto[0]) {
      await page.goto('/performance');
      await expect(page.getByText(equity[0].strategyName).first()).toBeVisible();
      await expect(page.getByText(crypto[0].strategyName).first()).toBeVisible();
    }
  });
});
