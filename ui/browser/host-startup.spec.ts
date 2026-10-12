import { test, expect } from '@playwright/test';

for (const width of [390, 1100]) test(`cold host failure is actionable before identity entry at ${width}px`, async ({ page }, info) => {
  await page.setViewportSize({width,height:720});
  await page.goto('/?host-failure=host_configuration&cold-host-failure');
  await expect(page.getByRole('heading', { name: 'The local host needs attention.' })).toBeVisible();
  await expect(page.getByText('This identity uses a managed host. Restore its registered configuration to reconnect.', { exact: true })).toHaveCount(1);
  await expect(page.getByLabel('Identity passphrase', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Create identity', exact: true })).toHaveCount(0);
  await page.screenshot({path:info.outputPath('cold-host-error.png'),fullPage:true});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.evaluate(() => (window as any).fixture.restoreHost());
  await page.getByRole('button', { name: 'Retry after configuration repair', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
});

for (const code of ['host_configuration', 'host_mismatch']) {
  test(`retained identity shows ${code} and reconnects after host recovery`, async ({ page }) => {
    await page.goto(`/?device-unlock&host-failure=${code}`);
    const passphrase = page.getByLabel('Identity passphrase', { exact: true });
    await passphrase.fill('fixture-passphrase');
    await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText(code === 'host_configuration' ? 'Restore its fleet host configuration' : 'does not match');
    await expect(page.getByRole('button', { name: 'Create identity', exact: true })).toHaveCount(0);
    await expect(page.getByRole('textbox', { name: 'Message or command' })).toHaveCount(0);
    const before = await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'unlock'));
    expect(before).toHaveLength(1);
    expect(before[0].create).toBe(false);
    await page.evaluate(() => (window as any).fixture.restoreHost());
    await passphrase.fill('fixture-passphrase');
    await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
    await expect(page.getByRole('alert')).toHaveCount(0);
  });
}
