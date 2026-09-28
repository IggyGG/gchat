// Run the existing ui/browser/server.mjs first; all conversations are local fixtures.
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import { mkdir, writeFile } from 'node:fs/promises';

const root = new URL('./', import.meta.url);
const path = name => fileURLToPath(new URL(name, root));
await mkdir(path('exports'), { recursive: true });
const browser = await chromium.launch({ headless: true });
const errors = [];
const summary = { fixture: 'ui/browser/fixture.ts', syntheticConversations: true, nativeAndroidVerified: false, assets: [] };
try {
  const context = await browser.newContext({ viewport: { width: 450, height: 730 }, deviceScaleFactor: 2, timezoneId: 'UTC', reducedMotion: 'reduce' });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  await page.clock.setFixedTime(new Date('2026-09-20T22:14:00Z'));
  await page.goto('http://127.0.0.1:1428');
  await page.locator('.active-title').waitFor();
  await page.evaluate(() => document.fonts.ready);
  const composer = page.getByRole('textbox', { name: 'Message or command' });
  const conversation = [
    ['peer', 'Anyone else miss the old chat rooms?'],
    ['self', 'The nicknames. The late nights. The people.'],
    ['peer', 'And that one channel that felt like home.'],
    ['self', 'Looks like we found it again :)'],
    ['peer', 'Same time tomorrow?'],
    ['self', "I'll be here."],
  ];
  let minute = 14;
  for (const [speaker, body] of conversation) {
    await page.clock.setFixedTime(new Date(`2026-09-20T22:${minute++}:00Z`));
    if (speaker === 'peer') await page.evaluate(text => window.fixture.receive(text), body);
    else { await composer.fill(body); await composer.press('Enter'); }
    await page.locator('.message').filter({ hasText: body }).waitFor();
  }
  await page.evaluate(() => window.fixture.acknowledge());
  await page.waitForTimeout(300);
  await composer.fill('Good to be back.');
  await composer.blur();
  const capture = async name => {
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    if (overflow) throw new Error(`Horizontal overflow in ${name}`);
    await page.screenshot({ path: path(`source/${name}.png`), animations: 'disabled' });
  };
  await capture('chat');
  await page.getByRole('button', { name: 'Channels', exact: true }).click();
  await page.getByRole('dialog', { name: 'Channels', exact: true }).waitFor();
  await capture('channels');
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Files: 1', exact: true }).click();
  await page.getByText('notes.txt', { exact: true }).waitFor();
  await capture('files');
  const invitation = await context.newPage();
  invitation.on('pageerror', error => errors.push(error.message));
  await invitation.goto('http://127.0.0.1:1428/?networks&fresh&device-unlock');
  await invitation.getByLabel('Identity passphrase', { exact: true }).fill('fixture-passphrase');
  await invitation.getByRole('button', { name: 'Reconnect', exact: true }).click();
  await invitation.locator('#network-invitation').waitFor();
  await invitation.evaluate(() => document.fonts.ready);
  if (await invitation.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error('Horizontal overflow in invitation');
  await invitation.screenshot({ path: path('source/invitation.png'), animations: 'disabled' });
  await context.close();

  const artwork = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  artwork.on('pageerror', error => errors.push(error.message));
  await artwork.goto(new URL('artboards.html', root).href);
  await artwork.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(image => image.decode()));
  });
  for (const id of ['feature', '01-conversation', '02-channels', '03-files', '04-invitation']) {
    await artwork.setViewportSize({ width: id === 'feature' ? 1024 : 1080, height: id === 'feature' ? 500 : 1920 });
    await artwork.evaluate(selected => {
      for (const board of document.querySelectorAll('.board')) {
        board.style.display = board.id === selected ? 'block' : 'none';
        board.style.margin = '0';
      }
      window.scrollTo(0, 0);
    }, id);
    const element = artwork.locator(`[id="${id}"]`);
    const bounds = await element.boundingBox();
    if (!bounds || bounds.width !== (id === 'feature' ? 1024 : 1080) || bounds.height !== (id === 'feature' ? 500 : 1920)) throw new Error(`Wrong dimensions: ${id}`);
    if (id !== 'feature') {
      const text = await element.locator('.sub').boundingBox();
      const screen = await element.locator('.screen').boundingBox();
      const caption = await element.locator('.caption').boundingBox();
      if (text.y + text.height >= screen.y || screen.y + screen.height >= caption.y) throw new Error(`Overlapping content: ${id}`);
    }
    const file = `${id}.${id === 'feature' ? 'png' : 'jpg'}`;
    await element.screenshot({ path: path(`exports/${file}`), ...(id === 'feature' ? {} : { type: 'jpeg', quality: 96 }), animations: 'disabled' });
    summary.assets.push({ file, width: bounds.width, height: bounds.height });
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await writeFile(path('validation.json'), JSON.stringify({ ...summary, pageErrors: errors, result: 'pass' }, null, 2) + '\n');
  console.log(JSON.stringify(summary, null, 2));
} finally {
  await browser.close();
}
