import { test, expect, type Page } from '@playwright/test';

const input = (page: Page) => page.getByRole('textbox', { name:'Message or command' });

async function aligned(page: Page) {
  await expect.poll(() => page.evaluate(() => {
    const bounds = (selector: string) => document.querySelector(selector)!.getBoundingClientRect();
    const conversation = ['.conversation-heading', '.conversation-content', '.conversation-footer'].map(bounds);
    const rails = [
      ['.channels.open .panel-heading', '.channels.open .channel-entries', '.channels.open .channel-actions'],
      ['.inspector .inspector-heading', '.inspector .users-list', '.inspector .inspector-actions'],
    ].filter(selectors => document.querySelector(selectors[0])?.getClientRects().length);
    return Math.max(...rails.flatMap(selectors => selectors.flatMap((selector, index) => {
      const rail = bounds(selector), center = conversation[index];
      return [Math.abs(rail.top - center.top), Math.abs(rail.bottom - center.bottom)];
    })), Math.abs(conversation[2].bottom - bounds('.workspace').bottom));
  })).toBeLessThanOrEqual(1);
  await expect(page.getByRole('button', { name:'Send', exact:true })).toBeInViewport({ ratio:1 });
}

for (const font of ['fixedsys', 'readable']) test(`shared rows follow topics, multiline drafts and collapsed rails in ${font}`, async ({ page }, info) => {
  await page.goto('/');
  await expect(page.locator('.active-title')).toHaveText('#general');
  await input(page).fill('/font ' + font); await input(page).press('Enter');
  for (const width of [1000,1100,1440]) {
    await page.setViewportSize({ width, height:720 });
    await expect(page.locator('.channels.docked.open')).toBeVisible();
    await expect(page.locator('.inspector.docked')).toBeVisible();
    await aligned(page);
  }
  await page.setViewportSize({ width:1100, height:720 });
  await page.evaluate(() => (window as any).fixture.setTopic(''));
  await expect(page.locator('.header-topic')).toHaveCount(0);
  await aligned(page);
  const compact = (await page.locator('.conversation-heading').boundingBox())!.height;
  await page.evaluate(() => (window as any).fixture.setTopic('A long channel topic · 日本語 '.repeat(40)));
  await expect(page.locator('.header-topic')).toContainText('日本語');
  await aligned(page);
  expect((await page.locator('.conversation-heading').boundingBox())!.height).toBeGreaterThan(compact);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.evaluate(() => (window as any).fixture.setCatchUp(12));
  await expect(page.locator('.header-topic[role=status]')).toContainText('12 updates');
  await aligned(page);
  await page.evaluate(() => (window as any).fixture.setCatchUp(null));
  await expect(page.locator('.header-topic[role=status]')).toHaveCount(0);
  const singleLine = (await page.locator('.conversation-footer').boundingBox())!.height;
  await input(page).fill('A multiline draft\n  keeps its spacing\nand grows the shared bottom row');
  await expect.poll(async () => (await page.locator('.conversation-footer').boundingBox())!.height).toBeGreaterThan(singleLine);
  await aligned(page);
  await page.screenshot({ path:info.outputPath('aligned-multiline.png') });
  await page.getByRole('button', { name:'Hide channels', exact:true }).click();
  await expect(page.locator('.channels')).toBeHidden(); await aligned(page);
  await page.getByRole('button', { name:'Close details', exact:true }).click();
  await expect(page.locator('.inspector')).toHaveCount(0); await aligned(page);
  await page.getByRole('button', { name:'Channels', exact:true }).click();
  await page.getByRole('button', { name:'Users: 2', exact:true }).click();
  await aligned(page);
  await input(page).fill(''); await aligned(page);
  await expect.poll(async () => (await page.locator('.conversation-footer').boundingBox())!.height).toBeCloseTo(singleLine,0);
  await page.screenshot({ path:info.outputPath('aligned-desktop.png') });
});

test('roster scrolling retains its bottom action and does not move the transcript or shared dividers', async ({ page }, info) => {
  await page.goto('/');
  await expect(page.locator('.active-title')).toHaveText('#general');
  await page.evaluate(() => {
    const f = (window as any).fixture;
    f.setMembers(Array.from({ length:80 }, (_, i) => ({ id:'member-'+i, nickname:'Member '+i, isSelf:i === 0, capabilities:[] })));
    f.seedMessages(80);
  });
  await expect(page.getByRole('button', { name:'Users: 80', exact:true })).toBeVisible();
  await expect(page.getByRole('log')).toContainText('Earlier message 79');
  await aligned(page);
  const scroll = await page.getByRole('log').evaluate(el => el.scrollTop);
  await page.locator('.users-list').hover(); await page.mouse.wheel(0,1000);
  await expect.poll(() => page.locator('.users-list').evaluate(el => el.scrollTop)).toBeGreaterThan(0);
  expect(await page.getByRole('log').evaluate(el => el.scrollTop)).toBe(scroll);
  await expect(page.getByRole('button', { name:'Channel recovery…', exact:true })).toBeInViewport({ ratio:1 });
  await aligned(page);
  await page.screenshot({ path:info.outputPath('scrolled-roster.png') });
  await page.getByRole('button', { name:'Channel recovery…', exact:true }).click();
  await expect(page.getByRole('heading', { name:'Channel recovery · general', exact:true })).toBeVisible();
});

test('shared rows survive desktop zoom, read-only context and a quiet empty roster footer', async ({ page }, info) => {
  await page.setViewportSize({ width:2200, height:1440 }); await page.goto('/?member');
  await expect(page.locator('.active-title')).toHaveText('#general');
  await page.evaluate(() => document.documentElement.style.zoom = '2');
  await expect(page.locator('.channels.docked.open')).toBeVisible();
  await aligned(page);
  await expect(page.getByRole('button', { name:'Channel recovery…', exact:true })).toHaveCount(0);
  await page.locator('.channels').getByRole('button', { name:/archive/ }).click();
  await expect(page.locator('.composer-context')).toContainText('Read-only');
  await input(page).fill('Keep this unsent\nwhile reading the archive');
  await aligned(page);
  await expect(page.getByRole('button', { name:'Send', exact:true })).toBeDisabled();
  await page.screenshot({ path:info.outputPath('aligned-zoom-archive.png') });
});
