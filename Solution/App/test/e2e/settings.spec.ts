import { test, expect } from '@playwright/test';
import { login, BASE } from './helper';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto(`${BASE}/dashboard/settings`);
  });

  test.describe('Profile Settings', () => {
    test('allows user to update their profile information', async ({ page }) => {
      const newName = 'Teacher One Updated';
      await page.getByLabel('Name').first().pressSequentially(newName, { delay: 100 });
      await page.getByRole('button', { name: 'Save Changes' }).click();

      await expect(page.locator('text=Success').first()).toBeVisible();

      await page.reload();

      await expect(page.getByLabel('Name')).toHaveValue(newName);
    });

    test('shows validation error for invalid profile information', async ({ page }) => {
      await page.getByLabel('Name').first().pressSequentially('a', { delay: 100 });
      await page.getByRole('button', { name: 'Save Changes' }).click();

      await expect(page.locator('text=Too short').first()).toBeVisible();
    });
  });

  test.describe('Security Settings', () => {
    test.beforeEach(async ({ page }) => {
      await page.getByRole('link', { name: 'Security' }).click();
      await expect(page).toHaveURL(`${BASE}/dashboard/settings/security`);
    });

    test('shows error when changing password with incorrect current password', async ({ page }) => {
      await page.getByPlaceholder('Current password').pressSequentially('wrongpassword', { delay: 100 });
      await page.getByPlaceholder('New password').pressSequentially('newpassword123', { delay: 100 });
      await page.getByRole('button', { name: 'Update Password' }).click();

      await expect(page.locator('text=Incorrect current password').first()).toBeVisible();
    });

    test('allows user to change their password', async ({ page }) => {
      await page.getByPlaceholder('Current password').pressSequentially('password123', { delay: 100 });
      await page.getByPlaceholder('New password').pressSequentially('newpassword123', { delay: 100 });
      await page.getByRole('button', { name: 'Update Password' }).click();

      await expect(page.locator('text=Your password has been updated.').first()).toBeVisible();

      // Log out and log back in with new password
      await page.getByRole('button', { name: 'Log Out' }).click();
      await expect(page).toHaveURL(`${BASE}/`);

      await page.goto(`${BASE}/login?institution=oxford`);
      await page.getByPlaceholder('Username').pressSequentially('teacher1', { delay: 100 });
      await page.getByPlaceholder('Password').pressSequentially('newpassword123', { delay: 100 });
      await page.getByRole('button', { name: 'Login' }).click();

      await expect(page).toHaveURL(`${BASE}/dashboard/updates`);
      await expect(page.locator('h1:has-text("Updates")').first()).toBeVisible();

      // Change password back to original for other tests
      await page.goto(`${BASE}/dashboard/settings/security`);
      await page.getByPlaceholder('Current password').pressSequentially('newpassword123', { delay: 100 });
      await page.getByPlaceholder('New password').pressSequentially('password123', { delay: 100 });
      await page.getByRole('button', { name: 'Update Password' }).click();
      await expect(page.locator('text=Your password has been updated.').first()).toBeVisible();
    });

    test('allows user to delete their account', async ({ page }) => {
      page.on('dialog', async (dialog) => {
        expect(dialog.message()).toContain('Are you absolutely sure you want to delete your account?');
        await dialog.accept();
      });

      await page.getByRole('button', { name: 'Delete Account' }).click();

      await expect(page).toHaveURL(`${BASE}/`);
      await expect(page.locator('text=Welcome to')).toBeVisible();

      // Verify user is deleted by trying to log in
      await page.goto(`${BASE}/login?institution=oxford`);
      await page.getByPlaceholder('Username').pressSequentially('teacher1', { delay: 100 });
      await page.getByPlaceholder('Password').pressSequentially('password123', { delay: 100 });
      await page.getByRole('button', { name: 'Login' }).click();
      await expect(page.locator('text=Invalid credentials').first()).toBeVisible();
    });
  });
});
