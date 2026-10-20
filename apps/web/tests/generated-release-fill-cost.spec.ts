import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the estimated fill cost shown beside the paper result.
 * The cost is labeled as an estimate and is not taken from the account.
 */

test('the dashboard shows the estimated fill cost beside the result', async ({ page }) => {
  await login(page);
  await page.goto('/dashboard');
  await expect(page.getByText('not taken from the account')).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Est. cost' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'After cost' })).toBeVisible();
});
