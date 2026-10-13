import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the risk-page crash.
 * The page used to call toFixed on fields the API does not send.
 */

test.describe('Risk page stays up', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('risk metrics use the fields the API sends', async ({ page }) => {
    const response = await page.request.get('/api/bot/risk-metrics?bot=quantshift-equity');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.openPositions).toEqual(expect.any(Number));
    expect(body.maxPositions).toBeGreaterThan(0);
    expect(body.dailyPnl).toEqual(expect.any(Number));
    expect(body.dailyLossLimit).toEqual(expect.any(Number));
    expect(body.maxDrawdown).toEqual(expect.any(Number));
    if (body.portfolioHeat != null) {
      expect(body.portfolioHeat).toEqual(expect.any(Number));
    }
  });

  test('risk page renders without a client exception', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(String(error)));

    await page.goto('/risk');
    await expect(page.getByRole('heading', { name: 'Risk Management' })).toBeVisible();
    await expect(page.getByRole('heading', { name: /^Circuit Breaker:/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Portfolio Heat' }).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Daily P&L' })).toBeVisible();
    await expect(page.getByText('client-side exception')).toHaveCount(0);
    expect(errors).toEqual([]);
  });
});
