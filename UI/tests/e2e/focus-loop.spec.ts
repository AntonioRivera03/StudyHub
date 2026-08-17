import { expect, test } from '@playwright/test';

test('completes and records an uncategorized focus session', async ({ page }) => {
  const sessionTitle = `Integration focus ${Date.now()}`;

  await page.goto('/focus');

  const existingCancel = page.getByRole('button', { name: 'Cancel' });
  const startFocus = page.getByRole('button', { name: 'Start focus' });
  await expect(existingCancel.or(startFocus)).toBeVisible();
  if (await existingCancel.isVisible()) {
    await existingCancel.click();
  }

  await expect(startFocus).toBeVisible();
  await page.getByLabel(/Focus title/).fill(sessionTitle);
  await page.getByRole('button', { name: 'Start focus' }).click();

  await expect(page.getByRole('button', { name: 'Pause' })).toBeVisible();
  await page.getByRole('button', { name: 'Pause' }).click();
  await expect(page.getByRole('button', { name: 'Resume' })).toBeVisible();
  await page.getByRole('button', { name: 'Resume' }).click();
  await expect(page.getByRole('button', { name: 'Pause' })).toBeVisible();

  await page.getByRole('button', { name: 'Finish session' }).click();
  await expect(page.getByRole('button', { name: 'Start focus' })).toBeVisible();

  await page.goto('/');
  await expect(page.getByText(sessionTitle)).toBeVisible();
  await expect(page.getByText('completed', { exact: true }).first()).toBeVisible();
});
