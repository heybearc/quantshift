import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Generated for the in-session stats refresh.
 * Opening a stats page loads once. Coming back to the tab loads again.
 */

async function showTab(page: import('@playwright/test').Page) {
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      get: () => 'visible',
    });
    document.dispatchEvent(new Event('visibilitychange'));
  });
}

test('dashboard and trades reload when the tab is visible again', async ({ page }) => {
  await login(page);

  let statusCalls = 0;
  let tradeCalls = 0;
  page.on('request', (request) => {
    const url = request.url();
    if (url.includes('/api/bot/status/all')) statusCalls += 1;
    if (url.includes('/api/bot/trades')) tradeCalls += 1;
  });

  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');
  await expect.poll(() => statusCalls, { timeout: 15000 }).toBeGreaterThan(0);
  const statusAfterLoad = statusCalls;

  await showTab(page);
  await expect.poll(() => statusCalls, { timeout: 10000 }).toBeGreaterThan(statusAfterLoad);

  await page.goto('/trades');
  await page.waitForLoadState('networkidle');
  await expect.poll(() => tradeCalls, { timeout: 15000 }).toBeGreaterThan(0);
  const tradesAfterLoad = tradeCalls;

  await showTab(page);
  await expect.poll(() => tradeCalls, { timeout: 10000 }).toBeGreaterThan(tradesAfterLoad);
});
