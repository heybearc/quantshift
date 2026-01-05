import { test, expect } from '@playwright/test';

/**
 * QUICK SMOKE TESTS - QuantShift Dashboard
 * Run these before every deployment
 */

const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'admin@test.com',
  password: process.env.TEST_USER_PASSWORD || 'admin123',
};

test.describe('QuantShift - Quick Smoke Tests', () => {
  test('Critical Path: Login → Dashboard', async ({ page }) => {
    // 1. Login
    await page.goto('/login');
    await page.fill('input[name="email"], input[type="email"]', TEST_USER.email);
    await page.fill('input[name="password"], input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });
    
    // 2. Verify dashboard loaded
    await expect(page.locator('body')).toBeVisible({ timeout: 5000 });
  });

  test('Dashboard loads without errors', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"], input[type="email"]', TEST_USER.email);
    await page.fill('input[name="password"], input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });
    
    // Page should be functional
    await expect(page.locator('body')).toBeVisible();
  });

  test('No critical JavaScript errors', async ({ page }) => {
    const errors: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    await page.goto('/login');
    await page.fill('input[name="email"], input[type="email"]', TEST_USER.email);
    await page.fill('input[name="password"], input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|home)/, { timeout: 10000 });
    
    await page.waitForTimeout(2000);
    
    const criticalErrors = errors.filter(e => 
      !e.includes('favicon') && 
      !e.includes('404') &&
      !e.includes('net::ERR_')
    );
    
    expect(criticalErrors.length).toBe(0);
  });
});
