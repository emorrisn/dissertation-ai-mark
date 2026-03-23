import type { Page } from 'playwright-core';

export const BASE = 'http://localhost:3000';

export async function login(page: Page) {
  await page.goto('http://localhost:3000/login?institution=oxford');
  await page.getByPlaceholder('Username').pressSequentially('teacher1', { delay: 100 });
  await page.getByPlaceholder('Password').pressSequentially('password123', { delay: 100 });
  await page.getByRole('button', { name: 'Login' }).click();
  await page.waitForURL(`${BASE}/dashboard/updates`);
}
