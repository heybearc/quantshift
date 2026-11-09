import { test, expect } from '@playwright/test';
import { TEST_USER } from './test-helpers';

/**
 * Generated for the API login fix.
 * A successful login returns a bearer token the bot routes accept.
 * A rejected login shows the API error text.
 */

test('login returns a bearer token and a rejected sign-in shows the API error', async ({ page, request }) => {
  const bad = await request.post('/api/auth/login', {
    data: { email: 'nobody-release@quantshift.io', password: 'not-a-real-password' },
  });
  expect(bad.status()).toBe(401);
  const badBody = await bad.json();
  expect(typeof badBody.error).toBe('string');
  expect(badBody.error.length).toBeGreaterThan(0);

  const good = await request.post('/api/auth/login', {
    data: { email: TEST_USER.email, password: TEST_USER.password },
  });
  expect(good.ok()).toBeTruthy();
  const body = await good.json();
  expect(body.token_type).toBe('bearer');
  expect(typeof body.access_token).toBe('string');
  expect(body.access_token.length).toBeGreaterThan(20);

  const status = await request.get('/api/bot/status/all', {
    headers: { Authorization: `Bearer ${body.access_token}` },
  });
  expect(status.status()).toBe(200);

  await page.goto('/login');
  await page.fill('input[id="email"]', 'nobody-release@quantshift.io');
  await page.fill('input[id="password"]', 'not-a-real-password');
  await page.click('button[type="submit"]');
  await expect(page.locator('.text-red-400')).toContainText('Invalid username/email or password');
});
