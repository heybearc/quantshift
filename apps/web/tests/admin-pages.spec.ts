import { test, expect } from '@playwright/test';
import { login } from './test-helpers';

test.describe('QuantShift - Admin Pages', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test.describe('Admin Settings Page', () => {
    test('Settings page loads successfully', async ({ page }) => {
      await page.goto('/admin/settings');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/admin\/settings/);
    });

    test('Settings page displays configuration options', async ({ page }) => {
      await page.goto('/admin/settings');
      await page.waitForLoadState('networkidle');
      
      // Check for settings content
      const hasSettings = await page.locator('text=/settings|configuration|email/i').count() > 0;
      expect(hasSettings).toBeTruthy();
    });
  });

  test.describe('Admin Invitations Page', () => {
    test('Invitations page loads successfully', async ({ page }) => {
      await page.goto('/admin/invitations');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/admin\/invitations/);
    });

    test('Invitations page displays invitation management', async ({ page }) => {
      await page.goto('/admin/invitations');
      await page.waitForLoadState('networkidle');
      
      // Check for invitation-related content
      const hasInvitations = await page.locator('text=/invite|invitation|email/i').count() > 0;
      expect(hasInvitations).toBeTruthy();
    });
  });

  test.describe('Admin Sessions Page', () => {
    test('Sessions page loads successfully', async ({ page }) => {
      await page.goto('/admin/sessions');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/admin\/sessions/);
    });

    test('Sessions page displays active sessions', async ({ page }) => {
      await page.goto('/admin/sessions');
      await page.waitForLoadState('networkidle');
      
      // Check for session-related content
      const hasSessions = await page.locator('text=/session|active|user/i').count() > 0;
      expect(hasSessions).toBeTruthy();
    });
  });

  test.describe('Admin Audit Logs Page', () => {
    test('Audit logs page loads successfully', async ({ page }) => {
      await page.goto('/admin/audit-logs');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/admin\/audit-logs/);
    });

    test('Audit logs page displays activity logs', async ({ page }) => {
      await page.goto('/admin/audit-logs');
      await page.waitForLoadState('networkidle');
      
      // Check for audit log content
      const hasLogs = await page.locator('text=/audit|log|activity|action/i').count() > 0;
      expect(hasLogs).toBeTruthy();
    });
  });

  test.describe('Admin Pending Users Page', () => {
    test('Pending users page loads successfully', async ({ page }) => {
      await page.goto('/admin/pending-users');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/admin\/pending-users/);
    });

    test('Pending users page displays user management', async ({ page }) => {
      await page.goto('/admin/pending-users');
      await page.waitForLoadState('networkidle');
      
      // Check for user management content
      const hasUsers = await page.locator('text=/user|pending|approve|reject/i').count() > 0;
      expect(hasUsers).toBeTruthy();
    });
  });

  test.describe('Admin Health Page', () => {
    test('Health page loads successfully', async ({ page }) => {
      await page.goto('/admin/health');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/admin\/health/);
    });

    test('Health page displays system status', async ({ page }) => {
      await page.goto('/admin/health');
      await page.waitForLoadState('networkidle');
      
      // Check for health status content
      const hasHealth = await page.locator('text=/health|status|system|database/i').count() > 0;
      expect(hasHealth).toBeTruthy();
    });
  });

  test.describe('Admin API Status Page', () => {
    test('API status page loads successfully', async ({ page }) => {
      await page.goto('/admin/api-status');
      await page.waitForLoadState('networkidle');
      
      await expect(page.locator('body')).toBeVisible();
      await expect(page).toHaveURL(/\/admin\/api-status/);
    });

    test('API status page displays endpoint status', async ({ page }) => {
      await page.goto('/admin/api-status');
      await page.waitForLoadState('networkidle');
      
      // Check for API status content
      const hasAPIStatus = await page.locator('text=/api|endpoint|status|response/i').count() > 0;
      expect(hasAPIStatus).toBeTruthy();
    });
  });

  test.describe('Admin Navigation', () => {
    test('Can navigate between admin pages', async ({ page }) => {
      await page.goto('/admin/settings');
      await page.waitForLoadState('networkidle');
      
      // Try navigating to different admin pages
      const adminPages = [
        '/admin/invitations',
        '/admin/sessions',
        '/admin/audit-logs',
        '/admin/health'
      ];
      
      for (const adminPage of adminPages) {
        await page.goto(adminPage);
        await page.waitForLoadState('networkidle');
        await expect(page.locator('body')).toBeVisible();
      }
    });
  });

  test.describe('Admin Error Handling', () => {
    test('Admin pages handle errors gracefully', async ({ page }) => {
      const errors: string[] = [];
      
      page.on('pageerror', (error) => {
        errors.push(error.message);
      });
      
      await page.goto('/admin/settings');
      await page.waitForLoadState('networkidle');
      
      // Check for critical errors
      const criticalErrors = errors.filter(e => 
        !e.includes('Warning') && 
        !e.includes('DevTools') &&
        !e.includes('chunk')
      );
      
      expect(criticalErrors.length).toBe(0);
    });
  });
});
