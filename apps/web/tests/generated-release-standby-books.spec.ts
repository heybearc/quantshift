import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the standby Kraken service.
 * The standby host can start Kraken, and the dashboard must still show the
 * primary books running.
 */

test.describe('Primary books stay up beside the standby Kraken service', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('equity, crypto, and kraken heartbeats are fresh', async ({ page }) => {
    const response = await page.request.get('/api/bot/health');
    expect(response.status()).toBe(200);
    const body = await response.json();
    const bots = body.bots as Array<{ botName: string; status: string; heartbeatAgeSeconds: number | null }>;

    for (const name of ['quantshift-equity', 'quantshift-crypto', 'quantshift-kraken']) {
      const bot = bots.find((row) => row.botName === name);
      expect(bot, name).toBeTruthy();
      expect(bot?.status).toBe('running');
      expect(bot?.heartbeatAgeSeconds).not.toBeNull();
      expect(bot?.heartbeatAgeSeconds ?? 999).toBeLessThan(180);
    }
  });
});
