import { test, expect, type Page } from '@playwright/test';
test('native remember choice defaults off and requires explicit consent', async ({ page }) => {
  await page.goto('/?device-unlock');
  await expect(page.getByLabel('Remember on this device')).not.toBeChecked();
  await page.getByLabel('Instance passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.unlockChoices)).toEqual([false]);
  await expect(page.locator('.active-title > span:first-child')).toHaveText('#general');
});
for (const width of [320, 760, 1100, 1440]) test(`channel drawer has visible open and close controls after unlock at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 });
  await page.goto('/?device-unlock');
  await page.getByLabel('Instance passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
  const toggle = page.getByRole('button', { name: 'Channels', exact: true });
  await expect(toggle).toBeVisible();
  await expect(toggle).toHaveText('Channels');
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  await expect(page.locator('#channel-navigation')).toBeHidden();
  const bounds = (await toggle.boundingBox())!;
  expect(bounds.width).toBeGreaterThanOrEqual(44);
  expect(bounds.height).toBeGreaterThanOrEqual(44);
  expect(bounds.x).toBeGreaterThanOrEqual(0);
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(width);
  await toggle.click();
  await expect(page.getByRole('dialog', { name: 'Channels', exact: true })).toBeVisible();
  await page.setViewportSize({ width, height: 700 });
  const close = page.getByRole('button', { name: 'Hide channels', exact: true });
  await expect(close).toBeVisible();
  await close.click();
  await expect(page.locator('#channel-navigation')).toBeHidden();
  await expect(toggle).toBeFocused();
  await toggle.click();
  await page.keyboard.press('Escape');
  await expect(page.locator('#channel-navigation')).toBeHidden();
  await expect(toggle).toBeFocused();
});
test('native vault failure keeps a successful unlock and shows the storage warning', async ({ page }) => {
  await page.goto('/?device-unlock&vault-failure');
  await page.getByLabel('Remember on this device').check();
  await page.getByLabel('Instance passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.unlockChoices)).toEqual([true]);
  await expect(page.locator('.active-title > span:first-child')).toHaveText('#general');
  await expect(page.getByText('Secure device storage unavailable; enter your passphrase after suspension.', { exact: true })).toBeVisible();
  await expect(page.locator('#gchat-password')).toHaveCount(0);
});
async function ready(page: Page, suffix = '') { await page.goto('/' + suffix); await expect(page.locator('.active-title > span:first-child')).toHaveText('#general'); }
async function command(page: Page, text: string) { const input = page.getByRole('textbox', { name: 'Message or command' }); await input.fill(text); await input.press('Enter'); }
test('channel details expose real topic, nickname and explicit owner departure choices', async ({ page }) => {
  await ready(page);
  await page.locator('.active-title').click();
  await page.getByLabel('Topic', { exact: true }).fill('Planning together');
  await page.getByRole('button', { name: 'Save topic', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit').at(-1))).toMatchObject({ conversation: 'channel/general', text: '/topic Planning together' });
  await page.locator('.active-title').click();
  await page.getByLabel('Your nickname here').fill('Iggy II');
  await page.getByRole('button', { name: 'Save nickname', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit').at(-1))).toMatchObject({ conversation: 'channel/general', text: '/nick Iggy II' });
  await page.locator('.active-title').click();
  await page.getByRole('button', { name: 'Leave channel…', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('Unconfirmed sends may not arrive');
  await expect(page.getByRole('button', { name: 'Close for everyone', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Transfer and leave', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit').at(-1))).toMatchObject({ conversation: 'channel/general', text: '/part --transfer peer' });
});

test('members get a real leave request without owner controls', async ({ page }) => {
  await ready(page, '?member');
  await page.locator('.active-title').click();
  await expect(page.getByRole('button', { name: 'Save topic', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Leave channel…', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('Membership removal waits for the owner');
  await expect(page.getByRole('button', { name: 'Close for everyone', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Leave channel', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit').at(-1))).toMatchObject({ conversation: 'channel/general', text: '/part' });
});

test('one invitation previews the other network and channel before joining', async ({ page }) => {
  await ready(page, '?networks');
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.getByRole('button', { name: 'Join or create a channel', exact: true }).click();
  await page.getByRole('button', { name: 'Join with an invitation or browse public channels', exact: true }).click();
  await page.getByLabel('Invitation', { exact: true }).fill('GCI1-valid-fixture');
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('Join #general on other.example');
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'networks' && r.request.kind === 'join'))).toBe(false);
  await page.getByLabel('Your nickname in this channel', { exact: true }).fill('New guest');
  await page.getByRole('button', { name: 'Join', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.locator('.network-group')).toHaveCount(2);
  await expect(page.locator('.network-group')).toContainText(['home.example', 'other.example']);
  await command(page, 'hello on this network');
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'networks' && r.request.kind === 'call' && r.request.request.kind === 'submit').at(-1)?.request)).toMatchObject({ network: 'b'.repeat(64), request: { conversation: 'channel/general', text: 'hello on this network' } });
});
test('one header, quiet default workspace, counters and keyboard-accessible tabs', async ({ page }) => {
  await ready(page);
  await expect(page.locator('.titlebar')).toHaveCount(1);
  await expect(page.locator('.toolbar, .topic, footer, .prompt')).toHaveCount(0);
  await expect(page.getByText('gchat-production')).toHaveCount(0);
  await expect(page.getByText('WINDOWS', { exact: true })).toHaveCount(0);
  await expect(page.getByText('NICKS', { exact: true })).toHaveCount(0);
  await expect(page.locator('.inspector')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Replace network invitation…' })).toHaveCount(0);
  await expect(page.locator('.channels')).toBeHidden();
  await expect(page.locator('.header-topic')).toHaveText('A little more room to talk.');
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
  await expect(page.locator('.active-title > span:first-child')).toHaveText('#general');
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
  await expect(page.locator('.active-title > span:first-child')).toHaveText('#general');
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
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.locator('.channels').getByRole('button', { name: /design/ }).click();
  await page.evaluate(() => (window as any).fixture.releaseUpload());
  await expect.poll(() => page.evaluate(() => (window as any).fixture.getFiles()[0]?.state)).toBe('complete');
  const record = await page.evaluate(() => (window as any).fixture.getFiles()[0]);
  expect(record.conversation).toBe('channel/general');
  await expect(page.getByRole('button', { name: /^Files:/ })).toHaveCount(0);
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.locator('.channels').getByRole('button', { name: /general/ }).click();
  await page.getByRole('button', { name: 'Files: 1', exact: true }).click();
  await expect(page.getByRole('tabpanel')).toContainText('sample.bin');
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.locator('.channels').getByRole('button', { name: /archive/ }).click();
  await expect(page.getByRole('button', { name: 'Share a file', exact: true })).toHaveCount(0);
});
for (const width of [320, 760, 1100, 1440]) test(`responsive layout ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 }); await ready(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Users: 2', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'Users 2' })).toBeVisible();
  await page.keyboard.press('Escape'); await expect(page.locator('.inspector')).toHaveCount(0);
  if (width <= 760) { await page.getByRole('button', { name: 'Channels', exact: true }).click(); await expect(page.getByRole('button', { name: 'Join or create a channel', exact: true })).toBeVisible(); await page.keyboard.press('Escape'); }
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

test.describe('phone navigation', () => {
  test.use({ hasTouch: true, isMobile: true, viewport: { width: 390, height: 844 } });

  for (const width of [320, 390]) test(`touch navigation keeps drafts and reachable actions at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await ready(page);
    const composer = page.getByRole('textbox', { name: 'Message or command' });
    await composer.fill('A draft for general');
    const targets = await page.locator('.titlebar button, .composer button').evaluateAll(nodes => nodes.map(node => {
      const bounds = node.getBoundingClientRect();
      return { label: node.getAttribute('aria-label') ?? node.textContent, width: bounds.width, height: bounds.height };
    }));
    for (const target of targets) {
      expect(target.width, String(target.label)).toBeGreaterThanOrEqual(44);
      expect(target.height, String(target.label)).toBeGreaterThanOrEqual(44);
    }
    await page.getByRole('button', { name: 'Channels', exact: true }).tap();
    await page.locator('.channels').getByRole('button', { name: /design/ }).tap();
    await expect(page.locator('.active-title > span:first-child')).toHaveText('#design');
    await expect(composer).not.toBeFocused();
    await expect(page.locator('.active-title')).toBeFocused();
    await composer.fill('A draft for design');
    await page.getByRole('button', { name: 'Channels', exact: true }).tap();
    await page.locator('.channels').getByRole('button', { name: /general/ }).tap();
    await expect(composer).toHaveValue('A draft for general');
    await expect(composer).not.toBeFocused();
    await page.getByRole('button', { name: 'Files: 1', exact: true }).tap();
    const save = page.getByRole('button', { name: 'Save file…', exact: true });
    await expect(save).toBeVisible();
    expect((await save.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    await page.getByRole('button', { name: 'Close details', exact: true }).tap();
    await expect(page.locator('.inspector')).toHaveCount(0);
    await page.getByRole('button', { name: 'Channels', exact: true }).tap();
    await page.getByRole('button', { name: 'Close navigation', exact: true }).tap({ position: { x: width - 8, y: 20 } });
    await expect(page.locator('.channels')).not.toBeVisible();
    await page.setViewportSize({ width: 844, height: width });
    await expect(composer).toHaveValue('A draft for general');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.setViewportSize({ width, height: 844 });
    await page.getByRole('button', { name: 'Channels', exact: true }).tap();
    await page.locator('.channels').getByRole('button', { name: /design/ }).tap();
    await expect(composer).toHaveValue('A draft for design');
  });

  test('keyboard viewport keeps the composer and invitation actions visible without following pinch zoom', async ({ page }) => {
    await page.addInitScript(() => {
      const viewport = Object.assign(new EventTarget(), { height: 844, offsetTop: 0, scale: 1 });
      Object.defineProperty(window, 'visualViewport', { configurable: true, value: viewport });
      Object.assign(window, { keyboardViewport: (height: number, offsetTop = 0, scale = 1) => {
        Object.assign(viewport, { height, offsetTop, scale });
        viewport.dispatchEvent(new Event('resize'));
      } });
    });
    await ready(page, '?networks');
    const composer = page.getByRole('textbox', { name: 'Message or command' });
    await composer.fill('Keep this draft through the keyboard');
    await page.evaluate(() => (window as any).keyboardViewport(360, 24));
    const bounds = await page.locator('.gchat').boundingBox();
    expect(bounds?.height).toBe(360);
    expect(bounds?.y).toBe(24);
    const send = await page.getByRole('button', { name: 'Send', exact: true }).boundingBox();
    expect(send!.y + send!.height).toBeLessThanOrEqual(384);
    await page.evaluate(() => (window as any).keyboardViewport(180, 80, 2));
    expect(await page.locator('.gchat').boundingBox()).toEqual(bounds);
    await page.evaluate(() => (window as any).keyboardViewport(360, 24));
    await page.getByRole('button', { name: 'Channels', exact: true }).tap();
    await page.getByRole('button', { name: 'Join or create a channel', exact: true }).tap();
    await page.getByRole('button', { name: 'Join with an invitation or browse public channels', exact: true }).tap();
    await page.getByLabel('Invitation', { exact: true }).fill('GCI1-valid-fixture');
    await page.getByRole('button', { name: 'Continue', exact: true }).tap();
    await page.getByLabel('Your nickname in this channel', { exact: true }).fill('Phone guest');
    const join = page.getByRole('button', { name: 'Join', exact: true });
    await join.scrollIntoViewIfNeeded();
    const action = await join.boundingBox();
    expect(action!.y).toBeGreaterThanOrEqual(24);
    expect(action!.y + action!.height).toBeLessThanOrEqual(384);
    expect(await page.getByLabel('Your nickname in this channel', { exact: true }).evaluate(node => getComputedStyle(node).fontSize)).toBe('16px');
    await page.getByRole('button', { name: 'Close dialog', exact: true }).tap();
    await expect(composer).toHaveValue('Keep this draft through the keyboard');
    await page.evaluate(() => (window as any).keyboardViewport(844));
    await expect(composer).toHaveValue('Keep this draft through the keyboard');
  });
});


test('original and recovered invitation share one overlay and one local result', async ({ page }) => {
  await ready(page);
  await command(page, '/invite');
  await expect(page.getByRole('dialog')).toContainText('Invite to #general');
  await expect.poll(() => page.evaluate(() => (window as any).fixture.checks())).toBeGreaterThan(0);
  await expect(page.getByRole('button', { name: 'Copy invitation', exact: true })).toHaveCount(1);
  await page.waitForTimeout(450);
  await expect(page.getByRole('button', { name: 'Copy invitation', exact: true })).toHaveCount(1);
  await page.getByRole('button', { name: 'Save as…', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('Saved to /chosen/gchat-invitation.txt');
  await page.getByRole('button', { name: 'Close details', exact: true }).click();
  await expect(page.locator('.local-results').getByRole('button', { name: 'Details', exact: true })).toHaveCount(1);
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeFocused();
  await command(page, '/invite');
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('.local-results').getByRole('button', { name: 'Details', exact: true })).toHaveCount(2);
});

test('Details explains a retained unknown outcome and refresh never resubmits', async ({ page }) => {
  await ready(page, '?saved-operation');
  await page.locator('.local-results').getByRole('button', { name: 'Details', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('saved-operation-001');
  await expect(page.getByRole('dialog')).toContainText('Outcome not confirmed');
  await page.getByRole('button', { name: 'Refresh status', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('No new result is available.');
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit'))).toEqual([]);
  await page.keyboard.press('Escape');
  await page.reload();
  await page.locator('.local-results').getByRole('button', { name: 'Details', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('saved-operation-001');
});

test('channel chooser defaults private and submits an explicit public choice', async ({ page }) => {
  await ready(page);
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.getByRole('button', { name: 'Join or create a channel', exact: true }).click();
  await page.getByRole('button', { name: 'Create a channel', exact: true }).click();
  await expect(page.getByLabel('Private — invitation required', { exact: true })).toBeChecked();
  await page.getByLabel('Public — discoverable when published to a directory', { exact: true }).check();
  await page.getByLabel('Channel name', { exact: true }).fill('#public');
  await page.getByLabel('Your nickname in this channel', { exact: true }).fill('Tester');
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit').at(-1)?.text)).toBe('/create --public #public Tester');
});


test('cancelling invitation Save as is neutral and keeps a closable result', async ({ page }) => {
  await ready(page, '?cancel-save');
  await command(page, '/invite');
  await page.getByRole('button', { name: 'Save as…', exact: true }).click();
  await expect(page.getByRole('dialog').getByText('Save cancelled.', { exact: true })).toBeVisible();
  await expect(page.getByText(/^Saved to /)).toHaveCount(0);
  await page.getByRole('button', { name: 'Close details', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
});
