import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the crypto book: a close is stored under the strategy that
 * opened it, not under one generic name.
 */

const STRATEGIES = [
  'BollingerBounce',
  'RSIMeanReversion',
  'KeltnerChannelStrategy',
  'VWAPReversionStrategy',
  'BreakoutMomentum',
  'MACrossoverStrategy',
  'DonchianBreakoutStrategy',
  'TradeConfidentSetup',
];

test.describe('Crypto strategy results', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('a crypto result names the strategy that opened it', async ({ page }) => {
    const response = await page.request.get('/api/bot/strategy-performance');
    expect(response.status()).toBe(200);
    const body = await response.json();
    const crypto = (body.strategies as Array<{ botName: string; strategyName: string }>).filter(
      (row) => row.botName.includes('crypto'),
    );
    expect(crypto.length).toBeGreaterThan(0);
    for (const row of crypto) {
      expect(STRATEGIES).toContain(row.strategyName);
    }

    const positions = await page.request.get('/api/bot/positions');
    expect(positions.status()).toBe(200);
    const openCrypto = ((await positions.json()).positions as Array<{ botName: string; strategy: string }>).filter(
      (position) => position.botName.includes('crypto'),
    );
    for (const position of openCrypto) {
      expect(STRATEGIES).toContain(position.strategy);
    }

    await page.goto('/performance');
    await expect(page.getByText(crypto[0].strategyName).first()).toBeVisible();
  });
});
