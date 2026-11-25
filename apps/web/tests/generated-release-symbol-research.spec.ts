import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the symbol library.
 * A member watches a listed name and pulls research without placing an order.
 */

test('a member watches a library symbol and opens research', async ({ page }) => {
  await login(page);
  await page.goto('/symbols');
  await expect(page.getByRole('heading', { name: 'Symbols' })).toBeVisible();
  await expect(page.getByText('Neither action places an order.')).toBeVisible();

  const alreadySaved = await page.getByRole('button', { name: 'NVDA', exact: true }).count();
  await page.locator('#symbol-library').selectOption('NVDA');

  await expect(page.getByText('Session trend. The right edge moves with the live quote.')).toBeVisible();
  await expect(page.getByText('Bid', { exact: false })).toBeVisible();
  await expect(page.getByText('Watching a quote does not place an order.')).toBeVisible();

  const researchResponse = page.waitForResponse(
    (response) => response.url().includes('/api/me/symbols/research') && response.request().method() === 'GET',
    { timeout: 30000 },
  );
  await page.getByRole('button', { name: 'Research' }).first().click();
  const response = await researchResponse;

  await expect(page.getByRole('heading', { name: 'NVDA research' })).toBeVisible();
  await expect(page.getByText('This does not place an order.')).toBeVisible();
  if (response.ok()) {
    await expect(page.getByText('Trend', { exact: true })).toBeVisible();
    await expect(page.getByText(/Rising|Falling|Flat/)).toBeVisible();
  } else {
    await expect(page.getByText(/could not be loaded|Enter a symbol/)).toBeVisible();
  }

  if (alreadySaved === 0) {
    const row = page.locator('div').filter({ has: page.getByRole('button', { name: 'NVDA', exact: true }) }).last();
    await row.getByRole('button', { name: 'Remove' }).click();
  }
});
