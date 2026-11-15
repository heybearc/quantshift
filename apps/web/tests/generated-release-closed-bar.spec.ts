import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the equity closed-bar fix.
 * Equity decides from the last finished daily bar and trades a symbol once
 * on that bar, so the same name must not close again inside ten minutes.
 */

const KNOWN_REGIMES = [
  'BULL_TRENDING',
  'BEAR_TRENDING',
  'HIGH_VOL_CHOPPY',
  'LOW_VOL_RANGE',
  'CRISIS',
  'UNKNOWN',
];

test.describe('Equity uses one decision per closed daily bar', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('equity is running on a known regime', async ({ page }) => {
    const response = await page.request.get('/api/bot/health');
    expect(response.status()).toBe(200);
    const body = await response.json();
    const equity = (body.bots as Array<{
      botName: string;
      status: string;
      heartbeatAgeSeconds: number | null;
      currentRegime: string;
    }>).find((row) => row.botName === 'quantshift-equity');

    expect(equity, 'quantshift-equity').toBeTruthy();
    expect(equity?.status).toBe('running');
    expect(equity?.heartbeatAgeSeconds).not.toBeNull();
    expect(equity?.heartbeatAgeSeconds ?? 999).toBeLessThan(180);
    expect(KNOWN_REGIMES).toContain(equity?.currentRegime);
  });

  test('equity does not close the same symbol twice inside ten minutes', async ({ page }) => {
    const response = await page.request.get('/api/bot/trades?botName=quantshift-equity&limit=40');
    expect(response.status()).toBe(200);
    const body = await response.json();
    const cutoff = Date.now() - 2 * 60 * 60 * 1000;
    const closes = new Map<string, number[]>();

    for (const trade of body.trades as Array<{ symbol: string; exitedAt: string | null }>) {
      if (!trade.exitedAt) continue;
      const exited = Date.parse(trade.exitedAt);
      if (Number.isNaN(exited) || exited < cutoff) continue;
      const times = closes.get(trade.symbol) ?? [];
      times.push(exited);
      closes.set(trade.symbol, times);
    }

    for (const [symbol, times] of closes) {
      times.sort((left, right) => left - right);
      for (let index = 1; index < times.length; index += 1) {
        expect(times[index] - times[index - 1], symbol).toBeGreaterThan(10 * 60 * 1000);
      }
    }
  });
});
