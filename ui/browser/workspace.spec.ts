import { test, expect, type Page } from '@playwright/test';
for (const width of [320, 390]) test(`mobile unlock action follows the complete device-storage explanation at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 });
  await page.goto('/?device-unlock');
  const hint = page.locator('#device-unlock-hint');
  const action = page.getByRole('button', { name: 'Reconnect', exact: true });
  await expect(hint).toBeVisible();
  await expect(action).toBeVisible();
  const explanation = (await hint.boundingBox())!;
  const button = (await action.boundingBox())!;
  expect(button.y).toBeGreaterThanOrEqual(explanation.y + explanation.height + 11);
  expect(button.x).toBeCloseTo(explanation.x, 0);
  expect(button.x + button.width).toBeLessThanOrEqual(width);
});
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
  await expect(toggle).toHaveText('#');
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
  await page.getByRole('button', { name: 'Join with an invitation', exact: true }).click();
  await page.getByLabel('Invitation', { exact: true }).fill('GCI1-valid-fixture');
  await page.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Join a channel', exact: true })).toContainText('Join #general on other.example');
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
  await expect(page.getByRole('dialog', { name: 'Files', exact: true })).toBeVisible();
  await expect(page.getByText('notes.txt', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Close dialog' }).click();
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
  await command(page, '/find clear space'); await expect(page.getByRole('textbox', { name: 'Find in #general', exact: true })).toHaveValue('clear space');
  await expect(page.locator('.search')).toContainText('1 matches'); await page.keyboard.press('Escape');
  await expect(page.locator('.search')).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeFocused();
  await page.getByRole('button', { name: 'Help and commands', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Commands', exact: true })).toContainText('/font [fixedsys|readable]');
  await expect(page.getByRole('dialog', { name: 'Commands', exact: true })).toContainText('/disconnect'); await page.keyboard.press('Escape');
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
  await expect(page.getByRole('button', { name: 'Files: 0', exact: true })).toBeVisible();
  await page.evaluate(() => (window as any).fixture.holdUpload());
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Share a file', exact: true }).click();
  await (await chooser).setFiles({ name: 'sample.bin', mimeType: 'application/octet-stream', buffer: Buffer.alloc(524288, 7) });
  await expect(page.getByRole('dialog', { name: 'Files', exact: true })).toBeVisible();
  await expect(page.getByRole('dialog', { name: 'Files', exact: true })).toContainText('Importing sample.bin');
  await page.getByRole('button', { name: 'Close dialog' }).click();
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.locator('.channels').getByRole('button', { name: /design/ }).click();
  await page.evaluate(() => (window as any).fixture.releaseUpload());
  await expect.poll(() => page.evaluate(() => (window as any).fixture.getFiles()[0]?.state)).toBe('complete');
  const record = await page.evaluate(() => (window as any).fixture.getFiles()[0]);
  expect(record.conversation).toBe('channel/general');
  await expect(page.getByRole('button', { name: 'Files: 0', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.locator('.channels').getByRole('button', { name: /general/ }).click();
  await page.getByRole('button', { name: 'Files: 1', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Files', exact: true })).toContainText('sample.bin');
  await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
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
  await expect(page.getByRole('button', { name: 'Help and commands', exact: true })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
  await page.getByRole('button', { name: 'Help and commands', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Commands', exact: true })).toContainText('/find');
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
    await page.getByRole('button', { name: 'Close dialog', exact: true }).tap();
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
    await page.getByRole('button', { name: 'Join with an invitation', exact: true }).tap();
    await page.getByLabel('Invitation', { exact: true }).fill('GCI1-valid-fixture');
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
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


test('original and recovered invitation share one focused output and one compact receipt', async ({ page }) => {
  await ready(page); await command(page, '/invite');
  const dialog = page.getByRole('dialog', { name: 'Invite to #general', exact: true });
  await expect(dialog).toBeVisible();
  expect(await page.evaluate(() => (window as any).fixture.checks())).toBe(0);
  await page.evaluate(() => (window as any).fixture.recoverInvitation());
  await expect(dialog.getByRole('button', { name: 'Copy invitation', exact: true })).toHaveCount(1);
  await page.waitForTimeout(450);
  await expect(page.locator('[data-operation]')).toHaveCount(1);
  await dialog.getByRole('button', { name: 'Save as…', exact: true }).click();
  await expect(dialog).toContainText('Saved to /chosen/gchat-invitation.txt');
  await dialog.getByRole('button', { name: 'Close dialog' }).click();
  await expect(page.locator('.transcript')).not.toContainText('GCI1-fixture-secret');
  await expect(page.locator('.transcript')).toContainText('Invitation created');
  await page.locator('.transcript').getByRole('button', { name: 'Details', exact: true }).click();
  await expect(dialog).toBeVisible(); await page.keyboard.press('Escape');
  await command(page, '/invite');
  await expect(dialog.getByRole('button', { name: 'Copy invitation', exact: true })).toHaveCount(1);
  await expect(page.locator('[data-operation]')).toHaveCount(2);
});

test('Details explains a retained unknown outcome and refresh never resubmits', async ({ page }) => {
  await ready(page, '?saved-operation');
  await page.locator('.transcript').getByRole('button', { name: 'Details', exact: true }).click();
  await expect(page.locator('.private-detail')).toContainText('saved-operation-001');
  await expect(page.locator('.private-detail')).toContainText('Outcome not confirmed');
  await page.getByRole('button', { name: 'Refresh status', exact: true }).click();
  await expect(page.locator('.private-detail')).toContainText('No new result is available.');
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit'))).toEqual([]);
  await page.keyboard.press('Escape');
  await page.reload();
  await page.locator('.transcript').getByRole('button', { name: 'Details', exact: true }).click();
  await expect(page.locator('.private-detail')).toContainText('saved-operation-001');
});

test('channel form defaults private and submits an explicit public choice', async ({ page }) => {
  await ready(page); await command(page, '/create');
  await expect(page.getByLabel('Who can join?')).toHaveValue('private');
  await page.getByLabel('Channel name', { exact: true }).fill('#public');
  await page.getByLabel('Who can join?').selectOption('public');
  await page.getByLabel('Your nickname in this channel', { exact: true }).fill('Tester');
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit'))).toEqual([]);
  await page.getByRole('button', { name: 'Create channel', exact: true }).click();
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit').at(-1)?.text)).toBe('/create --public #public Tester');
});


test('cancelling invitation Save as is neutral and keeps a closable result', async ({ page }) => {
  await ready(page, '?cancel-save'); await command(page, '/invite');
  await page.getByRole('button', { name: 'Save as…', exact: true }).click();
  await expect(page.getByRole('dialog')).toContainText('Save cancelled.');
  await expect(page.getByText(/^Saved to /)).toHaveCount(0);
  await page.getByRole('button', { name: 'Close dialog' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeVisible();
});

test('focused forms preserve the chat draft and never send field answers', async ({ page }) => {
  await ready(page); const input = page.getByRole('textbox', { name: 'Message or command' });
  await input.fill('my unsent draft');
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.getByRole('button', { name: 'Join or create a channel' }).click();
  await page.getByRole('button', { name: 'Create a channel', exact: true }).click();
  await page.getByLabel('Channel name', { exact: true }).fill('private field never sent');
  await page.keyboard.press('Escape');
  await expect(input).toHaveValue('my unsent draft');
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit'))).toEqual([]);
});
test('missing activity is omitted and panels overlay without changing message width', async ({ page }) => {
  await ready(page);
  const before = await page.locator('.conversation').boundingBox();
  await page.getByRole('button', { name: 'Users: 2' }).click();
  await expect(page.getByText('Unknown', { exact: true })).toHaveCount(0);
  await expect(page.locator('.users-list')).toContainText('you');
  expect((await page.locator('.conversation').boundingBox())!.width).toBe(before!.width);
});

test('old Status selection falls back to a conversation and last conversation survives reload', async ({ page }) => {
  await page.addInitScript(() => {
    if (!sessionStorage.getItem('gchat.navigation.ui-test-instance')) sessionStorage.setItem('gchat.navigation.ui-test-instance', JSON.stringify({ selected: null, positions: {} }));
  });
  await ready(page);
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.locator('.channels').getByRole('button', { name: /design/ }).click();
  await page.reload();
  await expect(page.locator('.active-title > span:first-child')).toHaveText('#design');
});

test('an app link waits through unlock and requires review and signed-network acceptance', async ({ page }) => {
  await page.goto('/?device-unlock&networks&app-link');
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'networks' && ['inspect', 'join'].includes(r.request.kind)))).toBe(false);
  await page.getByLabel('Instance passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
  await page.getByRole('button', { name: 'Review invitation', exact: true }).click();
  await expect(page.getByLabel('Invitation', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Continue', exact: true }).first().click();
  await expect(page.getByRole('dialog', { name: 'Join a channel', exact: true })).toContainText('Join #general on other.example');
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r: any) => r.kind === 'networks' && r.request.kind === 'join'))).toBe(false);
  await page.getByRole('button', { name: 'Close dialog' }).click();
  expect(await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage } }))).not.toContain('GCI1-');
});
test('pasted /join app link opens review without submitting it as a chat command', async ({ page }) => {
  await ready(page, '?networks');
  await command(page, '/join gcoms://join#GCI1-valid-fixture');
  await expect(page.getByLabel('Invitation', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit'))).toEqual([]);
});

test('native header exposes window actions without extra chrome on browsers or macOS', async ({ page }) => {
  await ready(page, '?native-shell');
  await page.evaluate(() => {
    Object.assign(window, { nativeActions: [] });
    for (const action of ['minimize', 'maximize', 'close']) window.addEventListener(`fixture-${action}`, () => (window as any).nativeActions.push(action));
  });
  await page.getByRole('button', { name: 'Minimize window', exact: true }).click();
  await page.getByRole('button', { name: 'Maximize or restore window', exact: true }).click();
  await page.getByRole('button', { name: 'Close window', exact: true }).click();
  expect(await page.evaluate(() => (window as any).nativeActions)).toEqual(['minimize', 'maximize', 'close']);
  await expect(page.locator('.resize')).toHaveCount(8);
  await ready(page, '?native-shell&mac');
  await expect(page.locator('.titlebar')).toHaveClass(/mac/);
  await expect(page.locator('.window-controls,.resize')).toHaveCount(0);
  await ready(page);
  await expect(page.locator('.window-controls,.resize,.drag-region')).toHaveCount(0);
});


test('bare header controls align the brand with the reconnect form', async ({ page }) => {
  await page.goto('/?device-unlock&native-shell');
  const brand = page.locator('.brand strong'), heading = page.getByRole('heading', { name: 'Reconnect this instance' });
  await expect(heading).toBeVisible();
  expect(Math.abs((await brand.boundingBox())!.x - (await heading.boundingBox())!.x)).toBeLessThanOrEqual(1);
  for (const selector of ['.network-button', '.help-button']) {
    const style = await page.locator(selector).evaluate(el => { const s = getComputedStyle(el); return [s.borderTopWidth,s.backgroundColor,s.borderRadius]; });
    expect(style).toEqual(['0px','rgba(0, 0, 0, 0)','0px']);
  }
  const dot = (await page.locator('.network-button').boundingBox())!, ghost = (await page.locator('.brand .ghost-mark').boundingBox())!;
  expect(Math.abs(dot.y + dot.height / 2 - ghost.y - ghost.height / 2)).toBeLessThanOrEqual(2);
});

for (const width of [320,1100]) test(`drawer rows fill the panel and carets stay outside content at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 }); await ready(page);
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  const drawer = (await page.locator('.channels.open').boundingBox())!, row = (await page.locator('.channels .chosen').boundingBox())!;
  expect(drawer.x + drawer.width - row.x - row.width).toBeLessThanOrEqual(2);
  const caret = (await page.getByRole('button', { name: 'Hide channels', exact: true }).boundingBox())!;
  expect(caret.x).toBeGreaterThanOrEqual(drawer.x + drawer.width - 2); expect(caret.x + caret.width).toBeLessThanOrEqual(width);
  await page.getByRole('button', { name: 'Hide channels', exact: true }).click();
  await page.getByRole('button', { name: 'Users: 2', exact: true }).click();
  const inspector = (await page.locator('.inspector').boundingBox())!, close = (await page.getByRole('button', { name: 'Close details', exact: true }).boundingBox())!;
  expect(close.x).toBeGreaterThanOrEqual(0); expect(close.x + close.width).toBeLessThanOrEqual(inspector.x + 2);
  expect(await page.locator('.inspector').evaluate(el => getComputedStyle(el).paddingLeft)).toBe('0px');
});

test('focused help opens guided actions or prepares commands without sending', async ({ page }) => {
  await ready(page);
  await page.getByRole('button', { name: 'Help and commands' }).click();
  const help = page.getByRole('dialog', { name: 'Commands', exact: true });
  await expect(help).toBeVisible();
  await help.getByRole('button', { name: '/find [text]', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Find in #general' })).toBeVisible();
  await expect(help).toHaveCount(0); await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Help and commands' }).click();
  await help.getByRole('button', { name: '/query', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toHaveValue('/query ');
  await expect(help).toHaveCount(0);
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit'))).toEqual([]);
  await page.getByRole('button', { name: 'Help and commands' }).click();
  await page.keyboard.press('Escape'); await expect(help).toHaveCount(0);
  await expect(page.locator('.transcript .commands')).toHaveCount(0);
});

async function activity(page: Page, suffix = '') {
  await ready(page,suffix); await page.getByRole('button', { name: /^Network:/ }).click();
  return page.getByRole('region', { name: 'Activity sharing', exact: true });
}
test('activity sharing reports pending, saved, disabled and retained state in settings', async ({ page }) => {
  const setting = await activity(page); await expect(setting.getByRole('heading')).toHaveText('Activity sharing: Off');
  await page.evaluate(() => (window as any).fixture.holdPresence());
  await setting.getByRole('button', { name: 'Enable activity sharing' }).click();
  await expect(setting.getByRole('button', { name: 'Saving…' })).toBeDisabled();
  await page.evaluate(() => (window as any).fixture.releasePresence());
  await expect(setting.getByRole('heading')).toHaveText('Activity sharing: On'); await expect(setting.getByRole('status')).toHaveText('Activity sharing enabled.');
  await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
  await page.getByRole('button', { name: /^Network:/ }).click(); await expect(setting.getByRole('heading')).toHaveText('Activity sharing: On');
  await setting.getByRole('button', { name: 'Turn activity sharing off' }).click();
  await expect(setting.getByRole('heading')).toHaveText('Activity sharing: Off'); await expect(setting.getByRole('status')).toHaveText('Activity sharing disabled.');
});
test('failed activity sharing stays visible and uncertain results check the original operation', async ({ page }) => {
  const setting = await activity(page,'?presence-result=rejected');
  await setting.getByRole('button', { name: 'Enable activity sharing' }).click();
  await expect(setting.getByRole('alert')).toContainText('Profile save failed'); await expect(setting.getByRole('heading')).toHaveText('Activity sharing: Off');
  await page.evaluate(() => (window as any).fixture.setPresenceOutcome('unknown'));
  await setting.getByRole('button', { name: 'Enable activity sharing' }).click();
  await expect(setting.getByRole('status')).toContainText('Change not confirmed');
  const count = await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit').length);
  await setting.getByRole('button', { name: 'Check result' }).click();
  await expect(setting.getByRole('status')).toHaveText('Activity sharing enabled.');
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit').length)).toBe(count);
});
test('activity settings target the selected network and keep a late response in its own scope', async ({ page }) => {
  const setting = await activity(page,'?networks&two-networks');
  await page.locator('#network-detail-selection').selectOption('b'.repeat(64));
  await page.evaluate(() => (window as any).fixture.holdPresence()); await setting.getByRole('button', { name: 'Enable activity sharing' }).click();
  await expect(setting.getByRole('button', { name: 'Saving…' })).toBeDisabled();
  await page.locator('#network-detail-selection').selectOption('a'.repeat(64)); await expect(setting.getByRole('heading')).toHaveText('Activity sharing: Off');
  await page.evaluate(() => (window as any).fixture.releasePresence());
  await expect.poll(() => page.evaluate(() => (window as any).fixture.presence('b'.repeat(64)))).toBe(true);
  await expect(setting.getByRole('heading')).toHaveText('Activity sharing: Off');
  await page.locator('#network-detail-selection').selectOption('b'.repeat(64)); await expect(setting.getByRole('heading')).toHaveText('Activity sharing: On');
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'networks' && r.request.kind === 'call' && r.request.request.kind === 'submit').at(-1).request)).toMatchObject({ network: 'b'.repeat(64), request: { conversation: null, text: '/presence on' } });
});

for (const width of [320, 390, 1100]) test(`conversation heading does not consume app-bar touch space at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 });
  await ready(page);
  const bar = (await page.locator('.titlebar').boundingBox())!;
  const title = (await page.locator('.active-title').boundingBox())!;
  expect(title.y).toBeGreaterThanOrEqual(bar.y + bar.height);
  await expect(page.locator('.titlebar .active-title')).toHaveCount(0);
  await page.getByRole('button', { name: 'Help and commands' }).click();
  await expect(page.getByRole('dialog', { name: 'Commands', exact: true })).toBeVisible();
});

test('shows immediate unlock feedback and accepts another message while sends are pending', async ({ page }) => {
  await page.goto('/?device-unlock&slow-unlock');
  await page.getByLabel('Instance passphrase', { exact: true }).fill('fixture-passphrase');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Unlocking…', exact: true })).toBeVisible();
  await expect(page.locator('.active-title')).toContainText('#general');
  await page.evaluate(() => (window as any).fixture.holdSends());
  await command(page, 'first pending message');
  await command(page, 'second pending message');
  await expect(page.locator('[data-operation]')).toHaveCount(2);
  await expect(page.getByRole('textbox', { name: 'Message or command' })).toBeEmpty();
  await expect(page.getByText('Saved operation · outcome not confirmed', { exact: true })).toHaveCount(0);
  await expect.poll(() => page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'submit' && !r.text.startsWith('/')).length)).toBe(2);
  await page.evaluate(() => (window as any).fixture.releaseSends());
});


test('compact invitation receipt precedes messages with exact operation and ACK reconciliation', async ({ page }) => {
  await ready(page); await command(page, '/invite');
  await expect(page.getByRole('dialog', { name: 'Invite to #general', exact: true })).toBeVisible();
  await page.keyboard.press('Escape');
  await page.evaluate(() => (window as any).fixture.holdSends());
  await command(page, 'Hello @Ada and @Iggy.');
  await expect(page.locator('[data-operation]').filter({ hasText: 'Hello @Ada' })).toHaveCount(1);
  await page.evaluate(() => (window as any).fixture.releaseSends());
  await expect(page.locator('.message.mine')).toContainText('Hello @Ada and @Iggy.');
  await expect(page.locator('[data-operation]').filter({ hasText: 'Hello @Ada' })).toHaveCount(0);
  await expect(page.locator('.message.mine .mention.self')).toHaveText('@Iggy');
  const colors = await page.locator('.message.mine').evaluate(el => ({ self:getComputedStyle(el.querySelector('.nick')!).color, mention:getComputedStyle(el.querySelector('.mention.self')!).color, peer:getComputedStyle(el.querySelector('.mention:not(.self)')!).color }));
  expect(colors.self).toBe(colors.mention); expect(colors.self).not.toBe(colors.peer);
  const invite = page.locator('[data-operation]').filter({ hasText: 'Invitation created' });
  expect((await invite.boundingBox())!.y).toBeLessThan((await page.locator('.message.mine').boundingBox())!.y);
  await expect(page.locator('.message.mine')).toContainText('accepted locally');
  await page.evaluate(() => (window as any).fixture.acknowledge());
  await expect(page.locator('.message.mine')).toContainText('delivered');
});

test('download has immediate conversation progress after the files panel closes', async ({ page }) => {
  await ready(page, '?offered-file');
  await page.getByRole('button', { name: 'Files: 1', exact: true }).click();
  await page.getByRole('button', { name: 'Download & share', exact: true }).click();
  await page.getByRole('button', { name: 'Close dialog', exact: true }).click();
  const transfer = page.locator('.transfer');
  await expect(transfer).toContainText('notes.txt');
  await expect(transfer).toContainText('Starting…');
  await expect(transfer.getByRole('progressbar')).toHaveAttribute('value', '1024');
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r: any) => r.kind === 'files' && r.request.action === 'accept').length)).toBe(1);
});

for (const width of [390, 1100]) test(`chat follows optimistic sends and resizing but respects scrollback at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 720 }); await ready(page);
  const log = page.getByRole('log');
  const gap = () => log.evaluate(el => el.scrollHeight-el.scrollTop-el.clientHeight);
  await page.evaluate(() => (window as any).fixture.seedMessages(80));
  await expect(log).toContainText('Earlier message 79');
  await expect.poll(gap).toBeLessThan(3);
  await page.evaluate(() => (window as any).fixture.holdSends());
  for (const text of ['first optimistic', 'second optimistic', 'third optimistic']) await command(page,text);
  await expect(page.locator('[data-operation]')).toHaveCount(3);
  await expect.poll(gap).toBeLessThan(3);
  await page.setViewportSize({ width, height: 400 }); await expect.poll(gap).toBeLessThan(3);
  await page.evaluate(() => (window as any).fixture.releaseSends());
  await expect(page.locator('.message.mine')).toHaveCount(3); await expect.poll(gap).toBeLessThan(3);
  await page.evaluate(() => (window as any).fixture.acknowledge());
  await expect(page.locator('.message.mine').last()).toContainText('delivered'); await expect.poll(gap).toBeLessThan(3);
  const box = (await log.boundingBox())!; await page.mouse.move(box.x+box.width/2,box.y+box.height/2); await page.mouse.wheel(0,-600);
  await expect(page.getByRole('button',{name:'Jump to latest'})).toBeVisible();
  const top = await log.evaluate(el => el.scrollTop);
  await page.evaluate(() => (window as any).fixture.receive('incoming while reading'));
  await expect(log).toContainText('incoming while reading');
  await expect.poll(() => log.evaluate(el => el.scrollTop)).toBeCloseTo(top,0);
  await command(page,'my reply follows latest'); await expect.poll(gap).toBeLessThan(3);
  await expect(page.getByRole('button',{name:'Jump to latest'})).toHaveCount(0);
});
for (const width of [320,390,1100]) test(`focused forms fit ${width}px and never reuse the chat input`, async ({ page }) => {
  await page.setViewportSize({width,height:720}); await ready(page,'?networks');
  const input=page.getByRole('textbox',{name:'Message or command'}); await input.fill('keep my draft');
  await page.getByRole('button',{name:'Channels',exact:true}).click();
  await page.getByRole('button',{name:'Join or create a channel'}).click();
  await page.getByRole('button',{name:'Join with an invitation',exact:true}).click();
  const screen=page.getByRole('dialog',{name:'Join a channel',exact:true});
  await expect(screen).toBeVisible(); await expect(page.getByLabel('Private answer')).toHaveCount(0);
  const bounds=(await screen.boundingBox())!;
  if(width<=640){expect(bounds.x).toBe(0);expect(bounds.width).toBe(width);expect(bounds.height).toBe(720);}
  else {expect(bounds.width).toBeLessThan(width);expect(bounds.x).toBeGreaterThan(0);}
  await page.getByLabel('Invitation',{exact:true}).fill('invalid'); await page.getByRole('button',{name:'Continue',exact:true}).click();
  await expect(screen.getByRole('alert')).toBeVisible();
  expect(await page.evaluate(()=>(window as any).fixture.requests.filter((r:any)=>r.kind==='submit'))).toEqual([]);
  await screen.getByRole('button',{name:'Close dialog'}).click(); await expect(input).toHaveValue('keep my draft');
});

test('notification setup is explicit, distinguishes registration and offers device settings', async ({page}) => {
  await page.goto('/?device-unlock&notifications');
  await page.getByLabel('Instance passphrase',{exact:true}).fill('fixture-passphrase'); await page.getByRole('button',{name:'Reconnect',exact:true}).click();
  const screen=page.getByRole('dialog',{name:'Notifications',exact:true});
  await expect(screen).toBeVisible();
  expect(await page.evaluate(()=>(window as any).fixture.pushRequests)).toEqual([]);
  await screen.getByRole('button',{name:'Enable notifications',exact:true}).click();
  await expect(screen).toContainText('Notifications: Registering');
  expect(await page.evaluate(()=>(window as any).fixture.pushRequests)).toEqual([true]);
  await page.evaluate(()=>(window as any).fixture.setPush({registered:true,message:'Notifications on'}));
  await expect(screen).toContainText('Notifications: On');
  await page.evaluate(()=>(window as any).fixture.setPush({permission:'denied',registered:false}));
  await expect(screen).toContainText('Permission needed');
  await screen.getByRole('button',{name:'Open device notification settings'}).click();
  expect(await page.evaluate(()=>(window as any).fixture.settingsOpened())).toBe(1);
  await screen.getByRole('button',{name:'Turn notifications off'}).click();
  await screen.getByRole('button',{name:'Not now'}).click();
  await page.reload(); await page.getByLabel('Instance passphrase',{exact:true}).fill('fixture-passphrase'); await page.getByRole('button',{name:'Reconnect',exact:true}).click();
  await expect(page.locator('.active-title')).toBeVisible(); await expect(screen).toHaveCount(0);
});
