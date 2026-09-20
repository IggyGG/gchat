import { test, expect, type Page } from '@playwright/test';
async function ready(page: Page, suffix = '') { await page.goto('/' + suffix); await expect(page.locator('.active-title')).toHaveText('#general'); }
async function command(page: Page, text: string) { const input = page.getByRole('textbox', { name: 'Message or command' }); await input.fill(text); await input.press('Enter'); }
test('one header, quiet default workspace, counters and keyboard-accessible tabs', async ({ page }) => {
  await ready(page);
  await expect(page.locator('.titlebar')).toHaveCount(1);
  await expect(page.locator('.toolbar, .topic, footer, .prompt')).toHaveCount(0);
  await expect(page.getByText('gchat-production')).toHaveCount(0);
  await expect(page.getByText('WINDOWS', { exact: true })).toHaveCount(0);
  await expect(page.getByText('NICKS', { exact: true })).toHaveCount(0);
  await expect(page.locator('.inspector')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Replace network invitation…' })).toHaveCount(0);
  await expect(page.locator('.channel-actions')).toContainText('Join…');
  await page.getByRole('button', { name: 'Users: 2', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'Users 2' })).toHaveAttribute('aria-selected', 'true');
  await page.getByRole('tab', { name: 'Users 2' }).press('ArrowRight');
  await expect(page.getByRole('tab', { name: 'Files 1' })).toBeFocused();
  await expect(page.getByText('notes.txt', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Close details' }).click();
  await expect(page.getByRole('button', { name: 'Users: 2', exact: true })).toBeFocused();
  await page.screenshot({ path: '../target/ui-layout-desktop.png' });
});
test('mandatory setup uses service validation and keeps established offline history', async ({ page }) => {
  await page.goto('/?fresh');
  await expect(page.getByRole('heading', { name: 'Connect to GChat' })).toBeVisible();
  await expect(page.locator('.channels, .composer, .inspector')).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Network invitation', exact: true }).fill('GCNI1-invalid');
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('signature rejected');
  await expect(page.locator('.composer')).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Network invitation', exact: true }).fill('GCNI1-valid-fixture');
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.locator('.active-title')).toHaveText('#general');
  await page.evaluate(() => (window as any).fixture.setNetwork('reconnecting'));
  await expect(page.getByRole('button', { name: 'Network: Reconnecting', exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
  await page.getByRole('button', { name: 'Network: Reconnecting', exact: true }).click();
  await page.getByRole('button', { name: 'Replace network invitation…' }).click();
  await page.getByRole('textbox', { name: 'Network invitation', exact: true }).fill('private-unsubmitted-text');
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Network: Reconnecting', exact: true }).click();
  await page.getByRole('button', { name: 'Replace network invitation…' }).click();
  await expect(page.getByRole('textbox', { name: 'Network invitation', exact: true })).toHaveValue('');
});
test('view commands, help, find, font persistence and existing lifecycle commands', async ({ page }) => {
  await ready(page);
  await command(page, '/font readable'); await expect(page.locator('.gchat')).toHaveClass(/readable/);
  await command(page, '/find clear space'); await expect(page.getByLabel('Find in #general', { exact: true })).toHaveValue('clear space');
  await expect(page.locator('.search')).toContainText('1 matches'); await page.keyboard.press('Escape');
  await expect(page.locator('.search')).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeFocused();
  await page.getByRole('button', { name: 'Help', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('/font [fixedsys|readable]');
  await expect(page.getByRole('dialog')).toContainText('/disconnect'); await page.keyboard.press('Escape');
  const sent = await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit'));
  expect(sent).toHaveLength(0);
  await page.reload(); await expect(page.locator('.gchat')).toHaveClass(/readable/);
  await expect(page.locator('.active-title')).toHaveText('#general');
  await command(page, '/say /font');
  await command(page, '/lock'); await expect(page.getByRole('heading', { name: 'Unlock chat' })).toBeVisible();
  await expect(page.locator('.inspector, .transcript, .composer')).toHaveCount(0);
});
test('paperclip works with zero files; closing and changing panels cannot cancel or retarget import', async ({ page }) => {
  await ready(page, '?empty');
  await expect(page.getByRole('button', { name: /^Files:/ })).toHaveCount(0);
  await page.evaluate(() => (window as any).fixture.holdUpload());
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Share a file', exact: true }).click();
  await (await chooser).setFiles({ name: 'sample.bin', mimeType: 'application/octet-stream', buffer: Buffer.alloc(524288, 7) });
  await expect(page.getByRole('tab', { name: /^Files/ })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('tabpanel')).toContainText('Importing sample.bin');
  await page.getByRole('button', { name: 'Close details' }).click();
  await page.locator('.channels').getByRole('button', { name: /design/ }).click();
  await page.evaluate(() => (window as any).fixture.releaseUpload());
  await expect.poll(() => page.evaluate(() => (window as any).fixture.getFiles()[0]?.state)).toBe('complete');
  const record = await page.evaluate(() => (window as any).fixture.getFiles()[0]);
  expect(record.conversation).toBe('channel/general');
  await expect(page.getByRole('button', { name: /^Files:/ })).toHaveCount(0);
  await page.locator('.channels').getByRole('button', { name: /general/ }).click();
  await page.getByRole('button', { name: 'Files: 1', exact: true }).click();
  await expect(page.getByRole('tabpanel')).toContainText('sample.bin');
  await page.locator('.channels').getByRole('button', { name: /archive/ }).click();
  await expect(page.getByRole('button', { name: 'Share a file', exact: true })).toHaveCount(0);
});
for (const width of [320, 760, 1100, 1440]) test(`responsive layout ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 }); await ready(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Users: 2', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'Users 2' })).toBeVisible();
  await page.keyboard.press('Escape'); await expect(page.locator('.inspector')).toHaveCount(0);
  if (width <= 760) { await page.getByRole('button', { name: 'Channels', exact: true }).click(); await expect(page.getByRole('button', { name: 'Create…', exact: true })).toBeVisible(); await page.keyboard.press('Escape'); }
  await page.screenshot({ path: `../target/ui-layout-${width}.png` });
});

test('200% text zoom keeps actions and transcript reachable', async ({ page }) => {
  await page.setViewportSize({ width: 760, height: 720 }); await ready(page);
  await page.evaluate(() => { document.documentElement.style.zoom = '2'; });
  await expect(page.getByRole('button', { name: 'Help', exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
  await page.getByRole('button', { name: 'Help', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('/find');
});
