import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the crypto and Kraken zone setup.
 * Those books may name TradeConfidentSetup. Equity stays on its own strategies.
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
];

const ZONE = 'TradeConfidentSetup';

test.describe('Crypto and Kraken zone setup', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('equity keeps its strategies while crypto and Kraken may use the zone setup', async ({ page }) => {
    const response = await page.request.get('/api/bot/strategy-performance');
    expect(response.status()).toBe(200);
    const rows = (await response.json()).strategies as Array<{ botName: string; strategyName: string }>;

    const equity = rows.filter((row) => row.botName.toLowerCase().includes('equity'));
    const crypto = rows.filter((row) => row.botName.toLowerCase().includes('crypto'));
    const kraken = rows.filter((row) => row.botName.toLowerCase().includes('kraken'));

    expect(equity.length).toBeGreaterThan(0);
    expect(crypto.length).toBeGreaterThan(0);
    for (const row of equity) {
      expect(row.strategyName).not.toBe(ZONE);
      expect(EARLIER).toContain(row.strategyName);
    }
    for (const row of [...crypto, ...kraken]) {
      expect([...EARLIER, ZONE]).toContain(row.strategyName);
    }

    await page.goto('/performance');
    await expect(page.getByText(equity[0].strategyName).first()).toBeVisible();
    await expect(page.getByText(crypto[0].strategyName).first()).toBeVisible();
  });
});
