import { test, expect } from '@playwright/test';

const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'test@quantshift.io',
  password: process.env.TEST_USER_PASSWORD || 'TestPass123!',
};

test('Debug login flow', async ({ page }) => {
  // Track console messages
  page.on('console', msg => console.log('BROWSER:', msg.text()));
  
  // Track network requests
  page.on('response', response => {
    if (response.url().includes('/api/auth/login')) {
      console.log('LOGIN API:', response.status(), response.statusText());
    }
  });
  
  // Go to login page
  console.log('Navigating to login page...');
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  console.log('Current URL:', page.url());
  
  // Fill form
  console.log('Filling form...');
  await page.waitForSelector('input[id="email"]', { state: 'visible' });
  await page.fill('input[id="email"]', TEST_USER.email);
  await page.fill('input[id="password"]', TEST_USER.password);
  
  // Click submit
  console.log('Clicking submit...');
  await page.click('button[type="submit"]');
  
  // Wait a bit and check URL
  await page.waitForTimeout(5000);
  console.log('After submit URL:', page.url());
  
  // Check for error messages
  const errorElement = await page.locator('.text-red-400, [class*="error"]').first();
  const errorVisible = await errorElement.isVisible().catch(() => false);
  if (errorVisible) {
    const errorText = await errorElement.textContent();
    console.log('Error message:', errorText);
  }
  
  // Take screenshot
  await page.screenshot({ path: 'test-results/debug-login.png', fullPage: true });
});
