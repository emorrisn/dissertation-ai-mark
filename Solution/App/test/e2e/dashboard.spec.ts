import { test, expect } from '@playwright/test';
import { login, BASE } from './helper';

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('navigates to Updates page', async ({ page }) => {
    await page.getByRole('link', { name: 'Updates' }).click();
    await expect(page).toHaveURL(`${BASE}/dashboard/updates`);
    await expect(page.locator('h1:has-text("Updates")')).toBeVisible();
  });

  test('navigates to Marking Sessions page', async ({ page }) => {
    await page.getByRole('link', { name: 'Marking Sessions' }).click();
    await expect(page).toHaveURL(`${BASE}/dashboard/marking`);
    await expect(page.locator('h1:has-text("Past Sessions")')).toBeVisible();
  });

  test('navigates to Settings page', async ({ page }) => {
    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page).toHaveURL(`${BASE}/dashboard/settings`);
    await expect(page.locator('h1:has-text("Settings")')).toBeVisible();
  });
});
