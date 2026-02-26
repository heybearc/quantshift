import { test, expect } from "@playwright/test";
import { login } from "./test-helpers";

const TEST_USER = {
  email: process.env.TEST_USER_EMAIL || "admin@quantshift.local",
  password: process.env.TEST_USER_PASSWORD || "Admin123!",
};

test.describe("QuantShift - Styling and Theme Validation", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("Dashboard has dark theme background", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    
    const bgColor = await page.evaluate(() => {
      const body = document.querySelector("body");
      return window.getComputedStyle(body!).backgroundColor;
    });
    
    // Should be dark (slate-900 or similar dark color)
    expect(bgColor).toMatch(/rgb\((15|16|17|18|19|20|21|22|23|24|25), (23|24|25|26|27|28|29|30), (42|43|44|45|46|47|48|49|50)\)/);
  });

  test("Positions page has dark theme", async ({ page }) => {
    await page.goto("/positions");
    await page.waitForLoadState("networkidle");
    
    const mainBg = await page.evaluate(() => {
      const main = document.querySelector("main");
      return window.getComputedStyle(main!).backgroundColor;
    });
    
    // Should not be white
    expect(mainBg).not.toBe("rgb(255, 255, 255)");
  });

  test("Trades page has dark theme", async ({ page }) => {
    await page.goto("/trades");
    await page.waitForLoadState("networkidle");
    
    const mainBg = await page.evaluate(() => {
      const main = document.querySelector("main");
      return window.getComputedStyle(main!).backgroundColor;
    });
    
    // Should not be white
    expect(mainBg).not.toBe("rgb(255, 255, 255)");
  });

  test("Performance page has dark theme", async ({ page }) => {
    await page.goto("/performance");
    await page.waitForLoadState("networkidle");
    
    const mainBg = await page.evaluate(() => {
      const main = document.querySelector("main");
      return window.getComputedStyle(main!).backgroundColor;
    });
    
    // Should not be white
    expect(mainBg).not.toBe("rgb(255, 255, 255)");
  });

  test("All pages have consistent navigation", async ({ page }) => {
    const pages = ["/dashboard", "/positions", "/trades", "/performance"];
    
    for (const pagePath of pages) {
      await page.goto(pagePath);
      await page.waitForLoadState("networkidle");
      
      // Navigation should be visible
      const nav = await page.locator("nav").first();
      await expect(nav).toBeVisible();
    }
  });
});

test.describe("QuantShift - Route Validation", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("Dashboard route exists and loads", async ({ page }) => {
    const response = await page.goto("/dashboard");
    expect(response?.status()).toBe(200);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main h1")).toContainText("Dashboard");
  });

  test("Positions route exists and loads", async ({ page }) => {
    const response = await page.goto("/positions");
    expect(response?.status()).toBe(200);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main h1")).toContainText("Positions");
  });

  test("Trades route exists and loads", async ({ page }) => {
    const response = await page.goto("/trades");
    expect(response?.status()).toBe(200);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main h1")).toContainText("Trade");
  });

  test("Performance route exists and loads", async ({ page }) => {
    const response = await page.goto("/performance");
    expect(response?.status()).toBe(200);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main h1")).toContainText("Performance");
  });

  test("Email notifications route exists and loads", async ({ page }) => {
    const response = await page.goto("/settings/notifications");
    expect(response?.status()).toBe(200);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main h1")).toContainText("Notification");
  });

  test("No 404 errors on main routes", async ({ page }) => {
    const routes = [
      "/dashboard",
      "/positions",
      "/trades",
      "/performance",
      "/settings",
      "/settings/notifications",
    ];

    for (const route of routes) {
      const response = await page.goto(route);
      expect(response?.status()).toBe(200);

      // Check for visible 404 error (not in Next.js internal data)
      const notFoundHeading = page.locator('h1:has-text("404")');
      await expect(notFoundHeading).not.toBeVisible();
      
      const notFoundMessage = page.locator('text="This page could not be found"');
      await expect(notFoundMessage).not.toBeVisible();
    }
  });
});

test.describe("QuantShift - Dashboard Data Display", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("Dashboard displays all key metrics", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    // Check for key metric labels
    await expect(page.locator("text=Total Portfolio")).toBeVisible();
    await expect(page.locator("text=Total P&L")).toBeVisible();
    await expect(page.locator("text=Open Positions")).toBeVisible();
  });

  test("Dashboard shows portfolio metrics", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(3000);

    // Check for always-visible combined metrics
    await expect(page.locator("text=Total Portfolio")).toBeVisible();
    await expect(page.locator("text=Total P&L")).toBeVisible();
    await expect(page.locator("text=Total Trades")).toBeVisible();
  });

  test("Currency values are properly formatted", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    // Check that currency values contain $ symbol
    const bodyText = await page.textContent("body");
    expect(bodyText).toContain("$");
  });
});
