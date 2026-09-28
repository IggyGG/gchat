// Start ui/browser/server.mjs first. Capture real shared UI using local sample data.
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
const require = createRequire(process.env.PW_DIR ? path.join(process.env.PW_DIR, 'package.json') : import.meta.url);
const { webkit, chromium } = require('playwright');
const root = new URL('./', import.meta.url);
const local = name => fileURLToPath(new URL(name, root));
await mkdir(local('source'), { recursive: true });
await mkdir(local('exports'), { recursive: true });
const formats = [
  { name: 'iphone', width: 1290, height: 2796, viewport: { width: 380, height: 760 }, scale: 3, displayType: 'APP_IPHONE_67' },
  { name: 'ipad', width: 2048, height: 2732, viewport: { width: 936, height: 1000 }, scale: 2, displayType: 'APP_IPAD_PRO_3GEN_129' },
];
const messages = [
  ['peer', 'Anyone else miss the old chat rooms?'],
  ['self', 'The nicknames. The late nights. The people.'],
  ['peer', 'And that one channel that felt like home.'],
  ['self', 'Looks like we found it again :)'],
  ['peer', 'Same time tomorrow?'],
  ['self', "I'll be here."],
];
const errors = [];
const report = { captureEngine: 'WebKit', nativeDeviceCapture: false, syntheticData: true, fixture: 'ui/browser/fixture.ts', assets: [] };
const browser = await webkit.launch({ headless: true });
try {
  for (const format of formats) {
    const context = await browser.newContext({ viewport: format.viewport, deviceScaleFactor: format.scale, hasTouch: true, isMobile: true, timezoneId: 'UTC', reducedMotion: 'reduce' });
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('http://127.0.0.1:1428');
    await page.locator('.active-title').waitFor();
    const composer = page.getByRole('textbox', { name: 'Message or command' });
    let minute = 14;
    for (const [speaker, text] of messages) {
      await page.clock.setFixedTime(new Date(`2026-09-20T22:${minute++}:00Z`));
      if (speaker === 'peer') await page.evaluate(body => window.fixture.receive(body), text);
      else { await composer.fill(text); await composer.press('Enter'); }
      await page.locator('.message').filter({ hasText: text }).waitFor();
    }
    await page.evaluate(() => window.fixture.acknowledge());
    await composer.fill('Good to be back.');
    await composer.blur();
    const capture = async (target, name) => {
      await target.evaluate(() => document.fonts.ready);
      if (await target.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error(`Overflow: ${format.name}/${name}`);
      await target.screenshot({ path: local(`source/${format.name}-${name}.png`), animations: 'disabled' });
    };
    await capture(page, 'chat');
    await page.getByRole('button', { name: 'Channels', exact: true }).click();
    await page.getByRole('dialog', { name: 'Channels', exact: true }).waitFor();
    await capture(page, 'channels');
    await page.getByRole('button', { name: 'Hide channels', exact: true }).click();
    await page.getByRole('button', { name: 'Files: 1', exact: true }).click();
    await page.getByText('notes.txt', { exact: true }).waitFor();
    await capture(page, 'files');
    const invitation = await context.newPage();
    invitation.on('pageerror', error => errors.push(error.message));
    await invitation.goto('http://127.0.0.1:1428/?networks&fresh&device-unlock');
    await invitation.getByLabel('Identity passphrase', { exact: true }).fill('fixture-passphrase');
    await invitation.getByRole('button', { name: 'Reconnect', exact: true }).click();
    await invitation.locator('#network-invitation').waitFor();
    await capture(invitation, 'invitation');
    await context.close();
  }
} finally { await browser.close(); }
const renderer = await chromium.launch({ headless: true });
try {
  const page = await renderer.newPage({ deviceScaleFactor: 1 });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(new URL('artboards.html', root).href);
  for (const format of formats) {
    await page.setViewportSize({ width: format.width, height: format.height });
    await page.evaluate(async device => {
      document.documentElement.dataset.device = device;
      for (const image of document.querySelectorAll('.screen')) image.src = image.getAttribute('src').replace(/source\/(iphone|ipad)-/, `source/${device}-`);
      await document.fonts.ready;
      await Promise.all([...document.images].map(image => image.decode()));
    }, format.name);
    for (const id of ['01-conversation', '02-channels', '03-files', '04-invitation']) {
      await page.evaluate(selected => {
        for (const board of document.querySelectorAll('.board')) { board.style.display = board.id === selected ? 'block' : 'none'; board.style.margin = '0'; }
        scrollTo(0, 0);
      }, id);
      const board = page.locator(`[id="${id}"]`);
      const bounds = await board.boundingBox();
      const text = await board.locator('.sub').boundingBox(), screen = await board.locator('.screen').boundingBox(), caption = await board.locator('.caption').boundingBox();
      if (bounds.width !== format.width || bounds.height !== format.height || text.y + text.height >= screen.y || screen.y + screen.height >= caption.y) throw new Error(`Invalid layout: ${format.name}/${id}`);
      const file = `${format.name}-${id}.jpg`;
      await board.screenshot({ path: local(`exports/${file}`), type: 'jpeg', quality: 96 });
      report.assets.push({ file, width: format.width, height: format.height, screenshotDisplayType: format.displayType });
    }
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await writeFile(local('validation.json'), JSON.stringify({ ...report, pageErrors: errors, result: 'pass' }, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally { await renderer.close(); }
