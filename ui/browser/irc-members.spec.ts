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
