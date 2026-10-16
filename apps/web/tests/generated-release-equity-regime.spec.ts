import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the equity book: the regime reading stays current after the close.
 * A trade-count halt used to freeze the last reading for the rest of the day.
 */

const KNOWN = [
  'BULL_TRENDING',
  'BEAR_TRENDING',
  'HIGH_VOL_CHOPPY',
  'LOW_VOL_RANGE',
  'CRISIS',
  'UNKNOWN',
];

test.describe('Equity regime after the close', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('the equity regime reading is a known label and still fresh', async ({ page }) => {
    const response = await page.request.get('/api/bot/regime?bot=quantshift-equity');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(KNOWN).toContain(body.regime);
    const ageMs = Date.now() - new Date(body.timestamp).getTime();
    expect(ageMs).toBeLessThan(30 * 60 * 1000);

    await page.goto('/regime');
    await expect(page.getByText('Latest equity regime reading')).toBeVisible();
    await expect(page.getByText(/Bull Trending|Bear Trending|High Vol Choppy|Low Vol Range|Crisis|Unknown/).first()).toBeVisible();
  });
});
