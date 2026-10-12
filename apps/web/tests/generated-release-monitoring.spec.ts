import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the monitoring-page correction.
 * Confirms the page shows the three bots, a real win rate, and risk bars that stay inside their cards.
 */

test.describe('Monitoring page readings', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('health, strategy results, and risk limits are readable', async ({ page }) => {
    const health = await page.request.get('/api/bot/health');
    expect(health.status()).toBe(200);
    const healthBody = await health.json();
    expect(healthBody.bots.length).toBeGreaterThanOrEqual(3);
    for (const bot of healthBody.bots) {
      expect(['running', 'stale']).toContain(bot.status);
      expect(bot.openPositions).toEqual(expect.any(Number));
      expect(bot.currentRegime).toMatch(/^[A-Z0-9_]+$/);
    }

    const strategies = await page.request.get('/api/bot/strategy-performance');
    expect(strategies.status()).toBe(200);
    const strategyBody = await strategies.json();
    expect(strategyBody.strategies.length).toBeGreaterThan(0);
    for (const row of strategyBody.strategies) {
      expect(row.strategyName).toBeTruthy();
      expect(row.winRate).toBeGreaterThanOrEqual(0);
      expect(row.winRate).toBeLessThanOrEqual(100);
      expect(row.totalPnl).toEqual(expect.any(Number));
    }

    const risk = await page.request.get('/api/bot/risk-metrics');
    expect(risk.status()).toBe(200);
    const riskBody = await risk.json();
    expect(riskBody.openPositions).toEqual(expect.any(Number));
    expect(riskBody.maxPositions).toBeGreaterThan(0);
    if (riskBody.portfolioHeat != null) {
      expect(riskBody.portfolioHeat).toBeGreaterThanOrEqual(0);
    }
  });

  test('monitoring page keeps risk bars inside the cards', async ({ page }) => {
    await page.goto('/monitoring');
    await expect(page.getByRole('heading', { name: 'Real-Time Monitoring' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Equity', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Crypto', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Kraken', exact: true })).toBeVisible();
    await expect(page.getByText('8333')).toHaveCount(0);
    await expect(page.getByText('83.3%')).toBeVisible();
    await expect(page.getByText('Bull Trending').first()).toBeVisible();

    const widths = await page.locator('.overflow-hidden.rounded-full > .rounded-full').evaluateAll((nodes) =>
      nodes.map((node) => Number.parseFloat((node as HTMLElement).style.width))
    );
    expect(widths.length).toBeGreaterThan(0);
    for (const width of widths) {
      expect(width).toBeGreaterThanOrEqual(0);
      expect(width).toBeLessThanOrEqual(100);
    }
  });
});
