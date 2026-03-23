import { test, expect } from '@playwright/test';
import { BASE, login } from './helper';

test.describe('Authentication Flow', () => {
  test('redirects to landing page if no institution is selected', async ({ page }) => {
    await page.goto(`${BASE}/login`);
    await page.locator('text=Magic Mark').waitFor({ state: 'visible', timeout: 15000 });
    await expect(page).toHaveURL(`${BASE}/`);
    await expect(page.locator('text=Welcome to')).toBeVisible();
  });

  test('does not allow login with invalid credentials', async ({ page }) => {
    await page.goto(`${BASE}/login?institution=oxford`);
    await page.locator('text=Account').waitFor({ state: 'visible', timeout: 15000 });
    await page.getByPlaceholder('Username').pressSequentially('invalid', { delay: 100 });
    await page.getByPlaceholder('Password').pressSequentially('invalid123', { delay: 100 });
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page.locator('text=Invalid credentials').first()).toBeVisible();
  });

  test('allows login with valid credentials', async ({ page }) => {
    await page.goto(`${BASE}/login?institution=oxford`);
    await page.getByPlaceholder('Username').pressSequentially('teacher1', { delay: 100 });
    await page.getByPlaceholder('Password').pressSequentially('password123', { delay: 100 });
    await page.getByRole('button', { name: 'Login' }).click();
    await expect(page).toHaveURL(`${BASE}/dashboard/updates`);
    await expect(page.locator('h1:has-text("Updates")')).toBeVisible();
  });

  test('logged in user can log out', async ({ page }) => {
    await login(page);
    await page.getByRole('button', { name: 'Log Out' }).click();
    await expect(page).toHaveURL(`${BASE}/`);
  });
});
