import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the volatility-break candle fix.
 * Coinbase and Kraken must both be running so that setup can see a daily
 * frame and an hourly frame. Equity is unchanged.
 */

const KNOWN_REGIMES = [
  'BULL_TRENDING',
  'BEAR_TRENDING',
  'HIGH_VOL_CHOPPY',
  'LOW_VOL_RANGE',
  'CRISIS',
  'UNKNOWN',
];

test.describe('Crypto and Kraken stay up for the volatility break', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('crypto and kraken heartbeats are fresh', async ({ page }) => {
    const response = await page.request.get('/api/bot/health');
    expect(response.status()).toBe(200);
    const body = await response.json();
    const bots = body.bots as Array<{ botName: string; status: string; heartbeatAgeSeconds: number | null }>;

    for (const name of ['quantshift-crypto', 'quantshift-kraken']) {
      const bot = bots.find((row) => row.botName === name);
      expect(bot, name).toBeTruthy();
      expect(bot?.status).toBe('running');
      expect(bot?.heartbeatAgeSeconds).not.toBeNull();
      expect(bot?.heartbeatAgeSeconds ?? 999).toBeLessThan(180);
    }
  });

  test('crypto and kraken regimes are known labels', async ({ page }) => {
    for (const name of ['quantshift-crypto', 'quantshift-kraken']) {
      const response = await page.request.get(`/api/bot/regime?botName=${name}`);
      expect(response.status()).toBe(200);
      const body = await response.json();
      if (body.regime != null) {
        expect(KNOWN_REGIMES).toContain(body.regime);
      }
    }
  });
});
