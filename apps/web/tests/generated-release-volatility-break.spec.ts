import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the volatility break on crypto and Kraken.
 * Those books may name VolatilityBreakoutSetup. Equity does not.
 */

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
  'BandSnapSetup',
];

test.describe('Volatility break on crypto and Kraken', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('equity does not use the volatility break', async ({ page }) => {
    const response = await page.request.get('/api/bot/strategy-performance');
    expect(response.status()).toBe(200);
    const rows = (await response.json()).strategies as Array<{ botName: string; strategyName: string }>;

    const equity = rows.filter((row) => row.botName.toLowerCase().includes('equity'));
    const crypto = rows.filter((row) => row.botName.toLowerCase().includes('crypto'));
    const kraken = rows.filter((row) => row.botName.toLowerCase().includes('kraken'));

    expect(equity.length).toBeGreaterThan(0);
    expect(crypto.length).toBeGreaterThan(0);
    for (const row of equity) {
      expect(row.strategyName).not.toBe('VolatilityBreakoutSetup');
      expect(row.strategyName).not.toBe('BandSnapSetup');
    }
    for (const row of [...crypto, ...kraken]) {
      expect(CRYPTO_STRATEGIES).toContain(row.strategyName);
    }

    await page.goto('/performance');
    await expect(page.getByText(crypto[0].strategyName).first()).toBeVisible();
  });
});
