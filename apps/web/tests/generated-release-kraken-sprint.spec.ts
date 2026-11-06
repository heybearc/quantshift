import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the separate Kraken sprint paper book.
 * It appears beside the three validation books and keeps its own cash.
 */

test('the sprint book is listed beside the other paper books', async ({ page }) => {
  await login(page);

  const status = await page.request.get('/api/bot/status/all');
  expect(status.status()).toBe(200);
  const statusBody = await status.json();
  const names = (statusBody.bots as Array<{ botName: string }>).map((bot) => bot.botName);
  expect(names).toEqual(expect.arrayContaining([
    'quantshift-equity',
    'quantshift-crypto',
    'quantshift-kraken',
    'quantshift-kraken-sprint',
  ]));

  const metrics = await page.request.get('/api/bot/metrics');
  expect(metrics.status()).toBe(200);
  const metricsBody = await metrics.json();
  const sprint = metricsBody.books.byBot['quantshift-kraken-sprint'];
  expect(sprint.start).toBe(5000);
  expect(sprint.account).toEqual(expect.any(Number));

  await page.goto('/dashboard');
  await expect(page.getByRole('button', { name: 'Kraken Sprint' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Sprint', exact: true })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Kraken', exact: true })).toBeVisible();
});
