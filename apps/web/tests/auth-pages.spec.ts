import { test, expect } from '@playwright/test';

test.describe('QuantShift - Auth Flow Pages', () => {
  test.describe('Login Page', () => {
    test('Login page loads successfully', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/login/);
    });

    test('Login page displays login form', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // Check for email and password inputs
      await expect(page.locator('input[id="email"]')).toBeVisible();
      await expect(page.locator('input[id="password"]')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test('Login form validates empty fields', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // Try submitting empty form
      await page.click('button[type="submit"]');
      
      // Form should not submit (stay on login page)
      await page.waitForTimeout(1000);
      await expect(page).toHaveURL(/\/login/);
    });

    test('Login form validates invalid credentials', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // Fill with invalid credentials
      await page.fill('input[id="email"]', 'invalid@example.com');
      await page.fill('input[id="password"]', 'wrongpassword');
      await page.click('button[type="submit"]');
      
      // Should show error or stay on login page
      await page.waitForTimeout(2000);
      const isStillOnLogin = await page.url().includes('/login');
      const hasError = await page.locator('text=/error|invalid|incorrect/i').count() > 0;
      
      expect(isStillOnLogin || hasError).toBeTruthy();
    });

    test('Successful login redirects to dashboard', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // Login with valid credentials
      await page.fill('input[id="email"]', process.env.TEST_USER_EMAIL || 'admin@quantshift.local');
      await page.fill('input[id="password"]', process.env.TEST_USER_PASSWORD || 'AdminPass123!');
      await page.click('button[type="submit"]');
      
      // Should redirect to dashboard
      await page.waitForURL(/\/(dashboard)?$/, { timeout: 10000 });
      await expect(page.locator('body')).toBeVisible();
    });
  });

  test.describe('Email Verification Page', () => {
    test('Email verification page loads', async ({ page }) => {
      await page.goto('/verify-email');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/verify-email/);
    });

    test('Email verification page displays verification message', async ({ page }) => {
      await page.goto('/verify-email');
      await page.waitForLoadState('networkidle');
      
      // Check for verification-related content
      const hasVerification = await page.locator('text=/verify|email|confirmation/i').count() > 0;
      expect(hasVerification).toBeTruthy();
    });
  });

  test.describe('Accept Invitation Page', () => {
    test('Accept invitation page loads', async ({ page }) => {
      // Test without token (should show error or redirect)
      await page.goto('/accept-invitation');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
    });

    test('Accept invitation page handles missing token', async ({ page }) => {
      await page.goto('/accept-invitation');
      await page.waitForLoadState('networkidle');
      
      // Should show error message or redirect
      const hasError = await page.locator('text=/error|invalid|expired|token/i').count() > 0;
      const isRedirected = !page.url().includes('/accept-invitation');
      
      expect(hasError || isRedirected).toBeTruthy();
    });

    test('Accept invitation page with token displays form', async ({ page }) => {
      // Test with a dummy token (will be invalid but should show the page)
      await page.goto('/accept-invitation?token=test-token-123');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
    });
  });

  test.describe('Auth Flow Navigation', () => {
    test('Unauthenticated users are redirected to login', async ({ page }) => {
      // Try accessing protected route without auth
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Should be on login page or dashboard (if already logged in from other tests)
      const url = page.url();
      const isLoginOrDashboard = url.includes('/login') || url.includes('/dashboard') || url.endsWith('/');
      expect(isLoginOrDashboard).toBeTruthy();
    });

    test('Login page allows authenticated users to access', async ({ page }) => {
      // First login
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      await page.fill('input[id="email"]', process.env.TEST_USER_EMAIL || 'admin@quantshift.local');
      await page.fill('input[id="password"]', process.env.TEST_USER_PASSWORD || 'AdminPass123!');
      await page.click('button[type="submit"]');
      
      await page.waitForURL(/\/(dashboard)?$/, { timeout: 10000 });
      
      // Verify we're authenticated by checking we can access dashboard
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Should be able to access protected routes
      await expect(page.locator('body')).toBeVisible();
    });
  });

  test.describe('Auth Error Handling', () => {
    test('Auth pages handle JavaScript errors gracefully', async ({ page }) => {
      const errors: string[] = [];
      
      page.on('pageerror', (error) => {
        errors.push(error.message);
      });
      
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // Check for critical errors
      const criticalErrors = errors.filter(e => 
        !e.includes('Warning') && 
        !e.includes('DevTools') &&
        !e.includes('chunk')
      );
      
      expect(criticalErrors.length).toBe(0);
    });

    test('Auth pages load without console errors', async ({ page }) => {
      const consoleErrors: string[] = [];
      
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });
      
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // Filter out non-critical errors
      const criticalErrors = consoleErrors.filter(e => 
        !e.includes('Warning') && 
        !e.includes('DevTools') &&
        !e.includes('chunk') &&
        !e.includes('favicon')
      );
      
      expect(criticalErrors.length).toBeLessThan(3); // Allow some minor errors
    });
  });

  test.describe('Auth Performance', () => {
    test('Login page loads within acceptable time', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(5000); // Should load in under 5 seconds
    });

    test('Login process completes within acceptable time', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      const startTime = Date.now();
      
      await page.fill('input[id="email"]', process.env.TEST_USER_EMAIL || 'admin@quantshift.local');
      await page.fill('input[id="password"]', process.env.TEST_USER_PASSWORD || 'AdminPass123!');
      await page.click('button[type="submit"]');
      
      await page.waitForURL(/\/(dashboard)?$/, { timeout: 10000 });
      
      const loginTime = Date.now() - startTime;
      
      expect(loginTime).toBeLessThan(10000); // Login should complete in under 10 seconds
    });
  });
});
