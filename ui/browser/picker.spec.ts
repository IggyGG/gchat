import { test, expect, type Page } from '@playwright/test';

async function unlock(page: Page) {
  await page.getByLabel('Instance passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
}

test('outgoing selection waits for same-profile unlock and keeps its original channel', async ({ page }) => {
  await page.goto('/?device-unlock&empty');
  await unlock(page);
  await expect(page.locator('.active-title')).toHaveText('#general');
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Share a file', exact: true }).click();
  const pending = await chooser;
  await page.evaluate(() => (window as any).fixture.suspend());
  await expect(page.getByRole('heading', { name: 'Reconnect this instance' })).toBeVisible();
  await pending.setFiles({ name: 'private-selection.txt', mimeType: 'text/plain', buffer: Buffer.from('fixture bytes') });
  await expect(page.getByText('private-selection.txt', { exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => (window as any).fixture.getFiles())).toEqual([]);
  await unlock(page);
  await expect(page.getByRole('button', { name: 'Continue selected file', exact: true })).toBeVisible();
  await page.locator('.channels').getByRole('button', { name: /design/ }).click();
  await page.getByRole('button', { name: 'Continue selected file', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.getFiles()[0]?.state)).toBe('complete');
  expect(await page.evaluate(() => (window as any).fixture.getFiles()[0]?.conversation)).toBe('channel/general');
});

test('invitation selection survives locked rendering without importing before consent', async ({ page }) => {
  await page.goto('/?device-unlock&fresh'); await unlock(page);
  await expect(page.getByRole('heading', { name: 'Connect to GChat' })).toBeVisible();
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Or choose an invitation file', exact: true }).click();
  const pending = await chooser;
  await page.evaluate(() => (window as any).fixture.suspend());
  await expect(page.getByRole('heading', { name: 'Reconnect this instance' })).toBeVisible();
  await pending.setFiles({ name: 'invitation.txt', mimeType: 'text/plain', buffer: Buffer.from('GCNI1-valid-fixture') });
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'import_network_invitation'))).toBe(false);
  await expect(page.getByRole('textbox', { name: 'Network invitation', exact: true })).toHaveCount(0);
  await unlock(page);
  await page.getByRole('button', { name: 'Continue selected file', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Network invitation', exact: true })).toHaveValue('GCNI1-valid-fixture');
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'import_network_invitation'))).toBe(false);
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.locator('.active-title')).toHaveText('#general');
});

for (const kind of ['invitation', 'outgoing']) test(`${kind} picker cancellation preserves manual unlock without a pending operation`, async ({ page }) => {
  await page.goto('/?device-unlock&empty' + (kind === 'invitation' ? '&fresh' : '')); await unlock(page);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: kind === 'invitation' ? 'Or choose an invitation file' : 'Share a file', exact: true }).click();
  const pending = await chooser;
  await page.evaluate(() => (window as any).fixture.suspend());
  await expect(page.getByRole('heading', { name: 'Reconnect this instance' })).toBeVisible();
  await pending.setFiles([]);
  await expect(page.getByText('File selection cancelled. Reconnect if this profile is locked.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reconnect', exact: true })).toBeVisible();
  await unlock(page);
  await expect(page.getByRole('button', { name: 'Continue selected file', exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => (window as any).fixture.getFiles())).toEqual([]);
});

test('a pending selection cannot migrate into a replaced profile', async ({ page }) => {
  await page.goto('/?device-unlock&empty'); await unlock(page);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Share a file', exact: true }).click();
  const pending = await chooser;
  await page.evaluate(() => (window as any).fixture.suspend());
  await expect(page.getByRole('heading', { name: 'Reconnect this instance' })).toBeVisible();
  await pending.setFiles({ name: 'original.txt', mimeType: 'text/plain', buffer: Buffer.from('fixture') });
  await page.evaluate(() => (window as any).fixture.replaceProfile('different-profile'));
  await expect(page.getByText('File selection discarded because the profile changed.', { exact: true })).toBeVisible();
  await unlock(page);
  await expect(page.getByRole('button', { name: 'Continue selected file', exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => (window as any).fixture.getFiles())).toEqual([]);
});

test('a channel removed while the picker is open cannot receive the pending file', async ({ page }) => {
  await page.goto('/?device-unlock&empty'); await unlock(page);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Share a file', exact: true }).click();
  const pending = await chooser;
  await page.evaluate(() => (window as any).fixture.suspend());
  await expect(page.getByRole('heading', { name: 'Reconnect this instance' })).toBeVisible();
  await pending.setFiles({ name: 'original.txt', mimeType: 'text/plain', buffer: Buffer.from('fixture') });
  await page.evaluate(() => (window as any).fixture.removeConversation('channel/general'));
  await unlock(page);
  await page.getByRole('button', { name: 'Continue selected file', exact: true }).click();
  await expect(page.getByText('The original conversation is unavailable. The file was not shared.', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => (window as any).fixture.getFiles())).toEqual([]);
});

test('expired picker ownership permits a fresh chooser and ignores its late old result', async ({ page }) => {
  await page.clock.install();
  await page.goto('/?device-unlock&fresh'); await unlock(page);
  const oldChooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Or choose an invitation file', exact: true }).click();
  const old = await oldChooser;
  await page.clock.fastForward(5 * 60 * 1000 + 1);
  await expect(page.getByText('File selection expired. Choose the file again.', { exact: true })).toBeVisible();
  const freshChooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Or choose an invitation file', exact: true }).click();
  const fresh = await freshChooser;
  await old.setFiles({ name: 'old.txt', mimeType: 'text/plain', buffer: Buffer.from('old invitation') });
  await expect(page.getByRole('button', { name: 'Continue selected file', exact: true })).toHaveCount(0);
  await fresh.setFiles({ name: 'fresh.txt', mimeType: 'text/plain', buffer: Buffer.from('GCNI1-valid-fixture') });
  await page.getByRole('button', { name: 'Continue selected file', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Network invitation', exact: true })).toHaveValue('GCNI1-valid-fixture');
});

test('a superseded unlock refresh never reads the invitation through stale UI state', async ({ page }) => {
  await page.goto('/?device-unlock&fresh'); await unlock(page);
  await page.evaluate(() => {
    const original = File.prototype.text;
    (window as any).pickerReads = 0;
    File.prototype.text = function() { (window as any).pickerReads++; return original.call(this); };
  });
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Or choose an invitation file', exact: true }).click();
  await (await chooser).setFiles({ name: 'private.txt', mimeType: 'text/plain', buffer: Buffer.from('GCNI1-valid-fixture') });
  await expect(page.getByRole('button', { name: 'Continue selected file', exact: true })).toBeVisible();
  await page.evaluate(() => { (window as any).fixture.holdSnapshots(); (window as any).fixture.suspend(); });
  await page.getByRole('button', { name: 'Continue selected file', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.pendingSnapshots())).toBeGreaterThan(0);
  await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await expect.poll(() => page.evaluate(() => (window as any).fixture.pendingSnapshots())).toBeGreaterThan(1);
  await page.evaluate(() => (window as any).fixture.releaseSupersededSnapshots());
  await expect.poll(() => page.evaluate(() => (window as any).pickerReads > 0 ||
    [...document.querySelectorAll('button')].some(button => button.textContent === 'Continue selected file' && !button.disabled))).toBe(true);
  expect(await page.evaluate(() => (window as any).pickerReads)).toBe(0);
  await page.evaluate(() => (window as any).fixture.releaseSnapshots());
  await expect(page.getByRole('heading', { name: 'Reconnect this instance' })).toBeVisible();
  await unlock(page);
  await page.getByRole('button', { name: 'Continue selected file', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Network invitation', exact: true })).toHaveValue('GCNI1-valid-fixture');
});
