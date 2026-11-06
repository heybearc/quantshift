import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the closed-trade window.
 * The performance summary counts finished trades for every book,
 * and a quiet hour still reports why a book stayed flat.
 */

const BOOKS = ['quantshift-equity', 'quantshift-crypto', 'quantshift-kraken'];

test.describe('Closed trades score the paper window', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('the performance summary comes from closed trades on every book', async ({ page }) => {
    for (const botName of ['', ...BOOKS]) {
      const path = botName
        ? `/api/bot/performance?botName=${botName}`
        : '/api/bot/performance';
      const response = await page.request.get(path);
      expect(response.status(), path).toBe(200);
      const body = await response.json();
      expect(body.summary.source).toBe('closed');
      expect(body.summary.totalTrades).toEqual(expect.any(Number));
      expect(body.summary.totalPnl).toEqual(expect.any(Number));
      expect(body.summary.winRate).toEqual(expect.any(Number));
      expect(body.curve).toHaveLength(body.summary.totalTrades);
      for (const point of body.curve) {
        expect(point.date).toEqual(expect.any(String));
        expect(point.value).toEqual(expect.any(Number));
      }
    }

    await page.goto('/performance');
    const empty = page.getByText('Metrics will populate once trades are closed.');
    const scored = page.getByText('Per closed trade');
    await expect(empty.or(scored)).toBeVisible();
  });

  test('a quiet hour explains a flat book without opening a trade', async ({ page }) => {
    const response = await page.request.get('/api/bot/quiet-hour');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(Array.isArray(body.books)).toBe(true);
    for (const book of body.books) {
      expect(['quantshift-crypto', 'quantshift-kraken']).toContain(book.botName);
      expect(book.checked).toEqual(expect.any(Number));
      expect(book.noSqueeze).toEqual(expect.any(Number));
    }

    await page.goto('/dashboard');
    if (body.books.length > 0) {
      await expect(page.getByText('Quiet hour')).toBeVisible();
      await expect(page.getByText('No squeeze:').first()).toBeVisible();
    }
  });
});
