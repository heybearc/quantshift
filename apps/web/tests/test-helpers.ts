import { Page, expect } from '@playwright/test';

/**
 * Test Helpers for QuantShift
 * Reusable utilities for E2E testing
 */

export const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || 'admin@quantshift.local',
  password: process.env.TEST_USER_PASSWORD || 'AdminPass123!',
};

/**
 * Login helper - performs authentication flow
 */
export async function login(page: Page) {
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
}

/**
 * Navigate to a specific page after login
 */
export async function navigateTo(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
}

/**
 * Wait for API response
 */
export async function waitForApiResponse(page: Page, urlPattern: string | RegExp) {
  return page.waitForResponse(
    response => {
      const url = response.url();
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern);
      }
      return urlPattern.test(url);
    },
    { timeout: 10000 }
  );
}

/**
 * Check if element exists and is visible
 */
export async function isVisible(page: Page, selector: string): Promise<boolean> {
  try {
    const element = page.locator(selector);
    await expect(element).toBeVisible({ timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * Get text content from element
 */
export async function getText(page: Page, selector: string): Promise<string> {
  const element = page.locator(selector);
  await expect(element).toBeVisible({ timeout: 5000 });
  return (await element.textContent()) || '';
}

/**
 * Wait for data to load (checks for loading indicators)
 */
export async function waitForDataLoad(page: Page) {
  // Wait for any loading indicators to disappear
  const loadingSelectors = [
    'text=Loading...',
    '[data-loading="true"]',
    '.loading',
    '.spinner'
  ];
  
  for (const selector of loadingSelectors) {
    try {
      await page.waitForSelector(selector, { state: 'hidden', timeout: 2000 });
    } catch {
      // Selector not found, continue
    }
  }
  
  await page.waitForTimeout(500);
}

/**
 * Take screenshot with timestamp
 */
export async function takeScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  await page.screenshot({ 
    path: `test-results/screenshots/${name}-${timestamp}.png`,
    fullPage: true 
  });
}

/**
 * Check for console errors (filtered)
 */
export function setupConsoleErrorTracking(page: Page): string[] {
  const errors: string[] = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  
  return errors;
}

/**
 * Filter out non-critical console errors
 */
export function filterCriticalErrors(errors: string[]): string[] {
  return errors.filter(e => 
    !e.includes('favicon') && 
    !e.includes('404') &&
    !e.includes('net::ERR_') &&
    !e.includes('Failed to load resource') &&
    !e.includes('_next/static') &&
    !e.includes('chunk') &&
    !e.includes('CSS')
  );
}

/**
 * Verify card exists with specific content
 */
export async function verifyCard(page: Page, title: string) {
  const card = page.locator('.bg-slate-800, .bg-white').filter({ hasText: title });
  await expect(card).toBeVisible({ timeout: 5000 });
  return card;
}

/**
 * Click and wait for navigation
 */
export async function clickAndNavigate(page: Page, selector: string) {
  await Promise.all([
    page.waitForNavigation({ timeout: 10000 }),
    page.click(selector)
  ]);
  await page.waitForLoadState('networkidle');
}

/**
 * Verify API endpoint is accessible
 */
export async function verifyApiEndpoint(page: Page, endpoint: string): Promise<boolean> {
  try {
    const response = await page.request.get(endpoint);
    return response.ok();
  } catch {
    return false;
  }
}

/**
 * Get dashboard stats
 */
export async function getDashboardStats(page: Page) {
  await waitForDataLoad(page);
  
  const stats = {
    activeBots: await getText(page, 'text=/\\d+ Active/i').catch(() => '0'),
    openPositions: await getText(page, 'text=/\\d+/').catch(() => '0'),
    todayTrades: await getText(page, 'text=/\\d+/').catch(() => '0'),
  };
  
  return stats;
}
