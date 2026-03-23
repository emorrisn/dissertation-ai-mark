import { test, expect } from '@playwright/test';
import { login, BASE } from './helper';

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('navigates to New Marking Sessions page', async ({ page }) => {
    await page.getByRole('link', { name: 'Marking Sessions' }).click();
    await expect(page).toHaveURL(`${BASE}/dashboard/marking`);
    await expect(page.locator('h1:has-text("Past Sessions")')).toBeVisible();
    await page.getByRole('link', { name: 'New Session' }).click();
    await expect(page).toHaveURL(`${BASE}/dashboard/marking/new`);
    await expect(page.locator('h1:has-text("Setup Session")')).toBeVisible();
  });
});
