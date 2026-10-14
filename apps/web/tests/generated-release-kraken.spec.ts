import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the Kraken book: shorts stay shorts, and a take-profit is stored.
 * The positions page has to show the side and the target.
 */

test.describe('Kraken position side and take profit', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('a short keeps its side and a target on the other side of the entry', async ({ page }) => {
    const response = await page.request.get('/api/bot/positions');
    expect(response.status()).toBe(200);
    const body = await response.json();
    const positions = body.positions as Array<{
      side: string;
      entryPrice: number;
      stopLoss: number | null;
      takeProfit: number | null;
      botName: string;
    }>;
    expect(positions.length).toBeGreaterThan(0);
    for (const position of positions) {
      expect(['long', 'short']).toContain(position.side);
    }

    const shorts = positions.filter((position) => position.side === 'short');
    expect(shorts.length).toBeGreaterThan(0);
    for (const position of shorts) {
      expect(position.takeProfit).toEqual(expect.any(Number));
      expect(position.stopLoss).toEqual(expect.any(Number));
      expect(position.stopLoss).toBeGreaterThan(position.entryPrice);
      expect(position.takeProfit).toBeLessThan(position.entryPrice);
    }

    await page.goto('/positions');
    await expect(page.getByRole('columnheader', { name: 'Side' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Take profit' })).toBeVisible();
    await expect(page.getByText('Short').first()).toBeVisible();
    await expect(page.getByText('Kraken').first()).toBeVisible();
  });
});
