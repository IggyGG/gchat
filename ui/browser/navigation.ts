import { expect, type Page } from '@playwright/test';

/** Workflows use the existing desktop rails or explicitly open a narrow drawer. */
export async function showChannels(page: Page) {
  const toggle = page.getByRole('button', { name:'Channels', exact:true });
  await expect(toggle).toBeVisible();
  if (await toggle.getAttribute('aria-expanded') !== 'true') await toggle.click();
  await expect(page.locator('#channel-navigation')).toBeVisible();
}
export async function showUsers(page: Page) {
  const toggle = page.getByRole('button', { name:/^Users:/ });
  await expect(toggle).toBeVisible();
  if (await toggle.getAttribute('aria-expanded') !== 'true') await toggle.click();
  await expect(page.locator('#user-navigation')).toBeVisible();
}
