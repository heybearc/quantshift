import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the regime page, drawdown formatting, and the Kraken optimization row.
 * The regime page must read the live payload, and drawdown must stay a signed percent.
 */

const regimeLabels: Record<string, string> = {
  BULL_TRENDING: 'Bull Trending',
  BEAR_TRENDING: 'Bear Trending',
  HIGH_VOLATILITY: 'High Volatility',
  HIGH_VOL_CHOPPY: 'High Volatility',
  LOW_VOLATILITY: 'Low Volatility',
  LOW_VOL_RANGE: 'Low Volatility',
  RANGE_BOUND: 'Range-Bound',
  CRISIS: 'Crisis',
  UNKNOWN: 'Unknown',
};

test.describe('Regime reading and drawdown', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('regime page shows the latest reading instead of the old accuracy claim', async ({ page }) => {
    const response = await page.request.get('/api/bot/regime');
    expect(response.status()).toBe(200);
    const payload = await response.json();
    const current = payload.current && typeof payload.current === 'object' ? payload.current : payload;
    expect(current.regime).toMatch(/^[A-Z0-9_]+$/);

    await page.goto('/regime');
    await expect(page.getByRole('heading', { name: 'Market Regime Analysis' })).toBeVisible();
    await expect(page.getByText('Latest equity regime reading')).toBeVisible();
    await expect(page.getByText('91.7% accuracy')).toHaveCount(0);
    await expect(page.getByText(regimeLabels[current.regime] ?? current.regime).first()).toBeVisible();
  });

  test('monitoring drawdown uses two decimal places', async ({ page }) => {
    await page.goto('/monitoring');
    await expect(page.getByText('Max Drawdown')).toBeVisible();
    await expect(page.getByText(/\d+\.\d{2}%/).first()).toBeVisible();
    await expect(page.getByText('8333')).toHaveCount(0);
  });

  test('optimization lists the Kraken paper strategy', async ({ page }) => {
    const response = await page.request.get('/api/bot/strategy-status');
    expect(response.status()).toBe(200);
    const rows = await response.json();
    expect(Array.isArray(rows)).toBe(true);
    expect(rows.some((row: { strategy_name?: string }) => String(row.strategy_name).includes('kraken'))).toBe(true);

    await page.goto('/optimization');
    await expect(page.getByRole('heading', { name: 'Optimization Monitoring' })).toBeVisible();
    await expect(page.getByText(/kraken/i).first()).toBeVisible();
  });
});
