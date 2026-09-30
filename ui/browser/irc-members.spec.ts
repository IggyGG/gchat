import { test, expect } from '@playwright/test';

for (const width of [390, 1100]) test(`hosted members retain scoped roles and actions at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 });
  await page.goto('/?hosted');
  await page.getByRole('button', { name: /Users/ }).first().click();
  await expect(page.getByRole('button', { name: 'Channel recovery…' })).toHaveCount(0);
  const member = page.getByRole('button', { name: /@Ada.*Away: Back later/ });
  await expect(member).toBeVisible();
  await member.click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests
    .filter((request: any) => request.kind === 'submit')
    .map((request: any) => [request.conversation, request.text]))).toEqual([
      ['channel/general', '/whois peer'],
    ]);
});

for (const width of [390, 1100]) test(`channel catch-up progress clears when current and stays private when locked at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 });
  await page.goto('/?hosted');
  await page.evaluate(() => (window as any).fixture.setCatchUp(0));
  const status = page.locator('.conversation-heading [role="status"]');
  await expect(status).toHaveText('Checking channel updates…');
  await page.evaluate(() => (window as any).fixture.setCatchUp(32));
  await expect(status).toHaveText('Catching up · 32 updates applied');
  await page.evaluate(() => (window as any).fixture.setCatchUp(64));
  await expect(status).toHaveText('Catching up · 64 updates applied');
  await page.evaluate(() => (window as any).fixture.setLocked(true));
  await expect(status).toHaveCount(0);
  await page.evaluate(() => { (window as any).fixture.setCatchUp(null); (window as any).fixture.setLocked(false); });
  await expect(status).toHaveCount(0);
});
