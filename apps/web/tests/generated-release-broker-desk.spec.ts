import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the personal broker desk.
 * A member connects from the approved catalog and submits an unknown broker
 * without placing a key on the request.
 */

test('a member opens the broker catalog and submits an unknown broker', async ({ page }) => {
  await login(page);
  await page.goto('/my-book');
  await page.getByRole('button', { name: 'My brokers' }).click();

  await expect(page.getByRole('heading', { name: 'Approved connections' })).toBeVisible();
  const alpaca = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Alpaca' }) });
  await expect(page.getByRole('heading', { name: 'Coinbase' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Kraken' })).toBeVisible();

  await alpaca.getByRole('button', { name: 'Connect' }).click();
  await expect(alpaca.getByText('API key ID')).toBeVisible();
  await expect(alpaca.getByText('API secret key')).toBeVisible();

  await expect(page.getByText('This records a request for review. It does not store a key or send an order.')).toBeVisible();
  const name = `Harbor Desk ${Date.now()}`;
  await page.getByPlaceholder('Broker name').fill(name);
  await page.getByRole('button', { name: 'Submit for review' }).click();
  await expect(page.getByText(`${name} was submitted for review.`)).toBeVisible();
  await expect(page.getByText(`${name} · submitted`)).toBeVisible();
});
