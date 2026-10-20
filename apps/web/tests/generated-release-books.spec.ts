import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the dashboard performance table.
 * Total P&L is closed trades plus the open book, and each book is listed.
 */

test('the dashboard shows closed and open results for each book', async ({ page }) => {
  await login(page);
  await page.goto('/dashboard');
  await expect(page.getByText('Closed trades + open book')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Equity' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Crypto' })).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Kraken' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'From start' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Closed' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Open' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Result' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Est. cost' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'After cost' })).toBeVisible();
});
