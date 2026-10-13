import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the account-equity drawdown correction.
 * The performance card must show a decline, not a gain, and the value
 * must stay inside a real account move rather than the old profit-peak ratio.
 */

test.describe('Performance drawdown', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('drawdown is an account decline without a plus sign', async ({ page }) => {
    const response = await page.request.get('/api/bot/performance');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.summary.maxDrawdown).toEqual(expect.any(Number));
    expect(body.summary.maxDrawdown).toBeGreaterThanOrEqual(0);
    expect(body.summary.maxDrawdown).toBeLessThan(100);

    await page.goto('/performance');
    const decline = page.getByText('Largest peak-to-trough decline of account equity');
    await expect(decline).toBeVisible();
    const card = page.locator('div.rounded-xl').filter({ has: decline });
    await expect(card.getByText(/\d+\.\d{2,4}%/)).toBeVisible();
    await expect(card.getByText(/\+\d/)).toHaveCount(0);
  });
});
