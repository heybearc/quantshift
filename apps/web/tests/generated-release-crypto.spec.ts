import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the crypto book: a position keeps the strategy that opened it.
 * The old book stored every close under one generic name.
 */

const STRATEGIES = [
  'BollingerBounce',
  'RSIMeanReversion',
  'KeltnerChannelStrategy',
  'VWAPReversionStrategy',
  'BreakoutMomentum',
  'MACrossoverStrategy',
  'DonchianBreakoutStrategy',
];

test.describe('Crypto position strategy', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('an open crypto position names the strategy that opened it', async ({ page }) => {
    const response = await page.request.get('/api/bot/positions');
    expect(response.status()).toBe(200);
    const body = await response.json();
    const crypto = (body.positions as Array<{ botName: string; strategy: string; symbol: string }>).filter(
      (position) => position.botName.includes('crypto'),
    );
    expect(crypto.length).toBeGreaterThan(0);
    for (const position of crypto) {
      expect(STRATEGIES).toContain(position.strategy);
    }

    await page.goto('/positions');
    await expect(page.getByText(crypto[0].strategy).first()).toBeVisible();
  });
});
