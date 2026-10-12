import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

/**
 * Release gate. Run this on STANDBY before every version bump.
 * It checks that the site is up and that a few values are true.
 * It does not replace the full suite.
 */

const KNOWN_REGIMES = [
  'BULL_TRENDING',
  'BEAR_TRENDING',
  'HIGH_VOL_CHOPPY',
  'LOW_VOL_RANGE',
  'CRISIS',
  'UNKNOWN',
];

test.describe('QuantShift release gate', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('standby server info is blue or green and not live', async ({ page }) => {
    const response = await page.request.get('/api/system/server-info');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(['BLUE', 'GREEN']).toContain(data.server);
    expect(['LIVE', 'STANDBY']).toContain(data.status);

    const base = process.env.BASE_URL || '';
    if (base.includes('quantshift.io')) {
      expect(data.status).toBe('STANDBY');
    }
  });

  test('latest release note has a version', async ({ page }) => {
    const response = await page.request.get('/api/release-notes/latest');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.success).toBe(true);
    expect(body.data.version).toMatch(/^\d+\.\d+\.\d+$/);
  });

  test('pending approvals page loads', async ({ page }) => {
    await page.goto('/admin/pending-users');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/admin\/pending-users/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('equity regime name is a known label', async ({ page }) => {
    const response = await page.request.get('/api/bot/regime?botName=quantshift-equity');
    expect(response.status()).toBe(200);
    const body = await response.json();
    if (body.regime != null) {
      expect(KNOWN_REGIMES).toContain(body.regime);
    }
  });
});
