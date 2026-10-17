import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the login session fix.
 * A missing access cookie renews from the saved session.
 * A dead session leaves the dashboard and returns to sign-in.
 */

test('an expired access cookie renews and a dead session returns to sign-in', async ({ page, context }) => {
  await login(page);
  await expect(page).toHaveURL(/\/dashboard/);

  const cookies = await context.cookies();
  const refresh = cookies.filter((cookie) => cookie.name === 'refresh_token');
  expect(refresh.length).toBeGreaterThan(0);

  await context.clearCookies();
  await context.addCookies(refresh);

  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByText('Failed to fetch bot status')).toHaveCount(0);

  const renewed = await context.cookies();
  expect(renewed.some((cookie) => cookie.name === 'access_token')).toBeTruthy();

  await context.clearCookies();
  await page.goto('/dashboard');
  await page.waitForURL(/\/login/, { timeout: 15000 });
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
});
