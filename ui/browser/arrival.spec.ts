import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { readInvitationCard, embedInvitationCard } from '../src/invitation-card';

const pixel = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64');

test('first arrival waits for identity state and requires matching passphrases', async ({ page }) => {
  await page.goto('/?device-unlock&first-run&slow-start');
  await expect(page.getByRole('heading', { name: 'Opening your space…' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Create identity', exact: true })).toHaveCount(0);
  await page.evaluate(() => (window as any).fixture.releaseSnapshots());
  await expect(page.getByRole('heading', { name: 'Make yourself at home.' })).toBeVisible();
  await page.getByLabel('Choose a passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByLabel('Confirm passphrase', { exact: true }).fill('different-passphrase');
  await page.getByRole('button', { name: 'Create identity', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('do not match');
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'unlock'))).toBe(false);
  await page.getByLabel('Confirm passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Create identity', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
});

test('exported PNG retains the invitation and stages before unlock without joining', async ({ page }, testInfo) => {
  await page.goto('/?networks&card-roundtrip');
  const input = page.getByRole('textbox', { name: 'Message or command' });
  await input.fill('/invite'); await input.press('Enter');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Save invitation card', exact: true }).click();
  const file = await download;
  const path = testInfo.outputPath('invitation.png'); await file.saveAs(path);
  expect(readInvitationCard(new Uint8Array(await readFile(path)))).toBe('GCI1-valid-fixture');
  await page.goto('/?networks&device-unlock');
  await page.getByLabel('Open invitation card', { exact: true }).setInputFiles(path);
  await expect(page.getByRole('status').filter({ hasText: 'Invitation ready.' })).toBeVisible();
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'networks' && r.request.kind === 'inspect'))).toBe(false);
  await page.getByLabel('Identity passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
  await page.getByRole('button', { name: 'Review invitation', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Only you: add a channel' })).toContainText('Join #general on other.example');
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'networks' && r.request.kind === 'join'))).toBe(false);
  await page.getByLabel('Private answer', { exact: true }).fill('Card guest');
  await page.getByLabel('Private answer', { exact: true }).press('Enter');
  await page.getByRole('button', { name: 'Join', exact: true }).click();
  await expect(page.locator('.network-group')).toHaveCount(2);
});

test('a PNG is only a container: invalid authority is refused by the service', async ({ page }) => {
  await page.goto('/?networks&fresh');
  await page.locator('#network-invitation-file').setInputFiles({ name: 'invitation.png', mimeType: 'image/png', buffer: Buffer.from(embedInvitationCard(pixel, 'GCI1-forged-fixture')) });
  await expect(page.getByRole('alert')).toContainText('Invitation signature rejected');
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'networks' && r.request.kind === 'join'))).toBe(false);
});

for (const width of [320, 1100]) test(`welcome fits ${width}px with reduced motion and visible keyboard focus`, async ({ page }, testInfo) => {
  await page.setViewportSize({ width, height: 800 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/?device-unlock');
  await page.getByLabel('Identity passphrase', { exact: true }).focus();
  await expect(page.getByLabel('Identity passphrase', { exact: true })).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const button = page.getByRole('button', { name: 'Reconnect', exact: true });
  expect(await button.evaluate(el => getComputedStyle(el).transitionDuration)).toBe('0s');
  await page.screenshot({ path: testInfo.outputPath(`welcome-${width}.png`), fullPage: true });
});

test('a late welcome-card read cannot cross a replaced profile', async ({ page }) => {
  await page.goto('/?networks&device-unlock');
  await expect(page.getByRole('heading', { name: 'Welcome back.' })).toBeVisible();
  await page.evaluate(() => {
    const original = File.prototype.arrayBuffer;
    File.prototype.arrayBuffer = async function () {
      await new Promise<void>(resolve => { (window as any).releaseCard = resolve; });
      return original.call(this);
    };
  });
  await page.getByLabel('Open invitation card', { exact: true }).setInputFiles({ name: 'invitation.png', mimeType: 'image/png', buffer: Buffer.from(embedInvitationCard(pixel, 'GCI1-valid-fixture')) });
  await expect(page.getByRole('button', { name: 'Opening card…', exact: true })).toBeVisible();
  await page.evaluate(() => (window as any).fixture.replaceProfile('replacement-profile'));
  await expect(page.getByRole('button', { name: 'Open invitation card', exact: true })).toBeEnabled();
  await page.evaluate(() => (window as any).releaseCard());
  await page.getByLabel('Identity passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Review invitation', exact: true })).toHaveCount(0);
});
