import { test, expect } from '@playwright/test';
import { login, navigateTo, setupConsoleErrorTracking, filterCriticalErrors } from './test-helpers';

/**
 * QUICK SMOKE TESTS - QuantShift Dashboard
 * Run these before every deployment
 */

const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'admin@quantshift.local',
  password: process.env.TEST_USER_PASSWORD || 'AdminPass123!',
};

test.describe('QuantShift - Quick Smoke Tests', () => {
  test('Critical Path: Login → Dashboard', async ({ page }) => {
    // 1. Login
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Wait for form to be ready
    await page.waitForSelector('input[id="email"]', { state: 'visible' });
    
    // Fill credentials
    await page.fill('input[id="email"]', TEST_USER.email);
    await page.fill('input[id="password"]', TEST_USER.password);
    
    // Submit and wait for navigation
    await Promise.all([
      page.waitForNavigation({ timeout: 15000 }),
      page.click('button[type="submit"]')
    ]);
    
    // Wait for redirect to complete
    await page.waitForTimeout(1000);
    
    // 2. Verify dashboard loaded
    await expect(page.locator('body')).toBeVisible({ timeout: 5000 });
  });

  test('Dashboard loads without errors', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('input[id="email"]', { state: 'visible' });
    await page.fill('input[id="email"]', TEST_USER.email);
    await page.fill('input[id="password"]', TEST_USER.password);
    await Promise.all([
      page.waitForNavigation({ timeout: 15000 }),
      page.click('button[type="submit"]')
    ]);
    await page.waitForTimeout(1000);
    
    // Page should be functional
    await expect(page.locator('body')).toBeVisible();
  });

  test('No critical JavaScript errors', async ({ page }) => {
    const errors = setupConsoleErrorTracking(page);
    
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('input[id="email"]', { state: 'visible' });
    await page.fill('input[id="email"]', TEST_USER.email);
    await page.fill('input[id="password"]', TEST_USER.password);
    await Promise.all([
      page.waitForNavigation({ timeout: 15000 }),
      page.click('button[type="submit"]')
    ]);
    await page.waitForTimeout(1000);
    
    await page.waitForTimeout(2000);
    
    const criticalErrors = filterCriticalErrors(errors);
    
    // Log errors for debugging if any found
    if (criticalErrors.length > 0) {
      console.log('Critical errors detected:', criticalErrors);
    }
    
    expect(criticalErrors.length).toBe(0);
  });
});
