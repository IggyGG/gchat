import { test, expect, type Page } from '@playwright/test';

async function ready(page: Page, query = '') {
  await page.goto('/' + query);
  await expect(page.locator('.active-title')).toHaveText('#general');
}
const input = (page: Page) => page.getByRole('textbox', { name:'Message or command' });
async function command(page: Page, text: string) { await input(page).fill(text); await input(page).press('Enter'); }
async function noOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  for (const selector of ['.conversation', '.transcript', '.composer']) {
    const bounds = await page.locator(selector).boundingBox();
    expect(bounds!.x).toBeGreaterThanOrEqual(0);
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(await page.evaluate(() => innerWidth));
  }
}

test('desktop rails are independent, remembered and become accessible phone drawers', async ({ page }) => {
  await page.setViewportSize({ width:1440, height:800 }); await ready(page);
  const channels = page.locator('#channel-navigation'), users = page.locator('#user-navigation');
  await expect(channels).toBeVisible(); await expect(users).toBeVisible();
  expect(await channels.getAttribute('role')).toBeNull();
  await input(page).fill('draft stays here');
  await page.getByRole('button', { name:'Hide channels', exact:true }).click();
  await expect(channels).toBeHidden(); await expect(users).toBeVisible();
  await page.reload(); await expect(channels).toBeHidden(); await expect(users).toBeVisible();
  await page.getByRole('button', { name:'Channels', exact:true }).click();
  await expect(channels).toBeVisible();
  await page.setViewportSize({ width:390, height:720 });
  await expect(channels).toBeHidden(); await expect(users).toHaveCount(0);
  const toggle = page.getByRole('button', { name:'Channels', exact:true });
  await expect(toggle).toContainText('2'); await toggle.click();
  await expect(page.getByRole('dialog', { name:'Channels', exact:true })).toBeVisible();
  await expect(page.locator('main.conversation')).toHaveAttribute('inert','');
  await page.keyboard.press('Escape'); await expect(toggle).toBeFocused();
  await noOverflow(page);
});

test('optimistic text has the same whitespace, sender and layout after acknowledgement', async ({ page }) => {
  await ready(page);
  await page.evaluate(() => (window as any).fixture.holdSends());
  const body = 'First line\n  two spaces\tand a tab\nこんにちは 👋 <b>literal</b>';
  await command(page, body);
  const row = page.locator('.message.mine');
  await expect(row.locator('.nick')).toHaveText('<Iggy>');
  expect(await row.locator('.body').textContent()).toBe(body);
  expect(await row.locator('.body').evaluate(el => getComputedStyle(el).whiteSpace)).toBe('pre-wrap');
  const pending = await row.locator('.body').boundingBox();
  await page.evaluate(() => (window as any).fixture.releaseSends());
  await expect(row).toContainText('accepted locally');
  expect(await row.locator('.body').textContent()).toBe(body);
  const accepted = await row.locator('.body').boundingBox();
  expect(accepted!.x).toBeCloseTo(pending!.x,0); expect(accepted!.height).toBeCloseTo(pending!.height,0);
  await page.evaluate(() => (window as any).fixture.acknowledge());
  await expect(row).toContainText('delivered'); await expect(row.locator('b')).toHaveCount(0);
});

test('inverse text uses a real contrasting theme background and resets correctly', async ({ page }) => {
  await ready(page);
  await page.evaluate(() => (window as any).fixture.receive('\x16inverse\x0f plain \x0304,02red on blue\x0f <script>literal</script>'));
  const body = page.locator('.message .body').last();
  const inverse = body.locator('span').filter({ hasText:/^inverse$/ });
  const colors = await inverse.evaluate(el => ({ ink:getComputedStyle(el).color, background:getComputedStyle(el).backgroundColor }));
  expect(colors.background).not.toBe('rgba(0, 0, 0, 0)'); expect(colors.background).not.toBe(colors.ink);
  await expect(body).toContainText('<script>literal</script>'); await expect(body.locator('script')).toHaveCount(0);
});

test('routine activity is grouped, full identities expand and uncertain sends have one honest row', async ({ page }) => {
  await ready(page);
  await page.evaluate(() => (window as any).fixture.setActivity(Array.from({ length:30 }, (_,i) => ({ id:'join-'+i, conversation:'channel/general', kind:'join', text:`Guest ${i} (${'a'.repeat(64)}) joined`, timestamp:1900000000+i }))));
  await expect(page.locator('.activity')).toHaveCount(1);
  await expect(page.locator('.activity summary')).toHaveText('*** 30 channel updates');
  await page.locator('.activity summary').click();
  await expect(page.locator('.activity p')).toHaveCount(30);
  await expect(page.locator('.activity p').first()).toContainText('a'.repeat(64));
  await page.evaluate(() => (window as any).fixture.setSendOutcome('outcome_unknown'));
  await command(page,'uncertain message');
  await expect(page.locator('.message.mine')).toHaveCount(1);
  await expect(page.locator('.message.mine')).toContainText('Outcome unconfirmed');
  await expect(page.getByText('Checking outcome…',{exact:true})).toHaveCount(0);
  await expect(page.locator('.retry')).toHaveCount(0);
  await page.getByRole('button',{name:'Details for message from Iggy'}).click();
  await expect(page.getByRole('dialog')).toContainText('Outcome not confirmed');
  const before = await page.evaluate(() => (window as any).fixture.requests.filter((r:any)=>r.kind==='submit').length);
  await page.getByRole('button',{name:'Refresh status',exact:true}).click();
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r:any)=>r.kind==='submit').length)).toBe(before);
});

test('caret completion preserves suffix, keyboard selection does not send and history respects editing', async ({ page }) => {
  await ready(page);
  await input(page).fill('hello Ad today');
  await input(page).evaluate((el:HTMLTextAreaElement) => el.setSelectionRange(8,8));
  await input(page).press('Tab'); await expect(input(page)).toHaveValue('hello Ada today');
  await page.evaluate(() => (window as any).fixture.setMembers([{id:'self',nickname:'Iggy',isSelf:true,capabilities:[]},{id:'ada',nickname:'Ada',isSelf:false,capabilities:[]},{id:'alan',nickname:'Alan',isSelf:false,capabilities:[]} ]));
  await expect(page.getByRole('button',{name:'Users: 3',exact:true})).toBeVisible();
  await input(page).fill('A'); await input(page).press('Tab');
  await expect(page.getByRole('listbox',{name:'Command completions'})).toBeVisible();
  await input(page).press('Tab'); await input(page).press('Enter');
  await expect(input(page)).toHaveValue('Alan: ');
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r:any)=>r.kind==='submit').length)).toBe(0);
  await page.evaluate(() => (window as any).fixture.setInputHistory([{conversation:'channel/general',text:'previous input'}]));
  await input(page).fill('keep this draft');
  await input(page).evaluate((el:HTMLTextAreaElement) => el.setSelectionRange(4,4));
  await input(page).press('ArrowUp'); await expect(input(page)).toHaveValue('keep this draft');
  await input(page).press('Home'); await input(page).press('ArrowUp'); await expect(input(page)).toHaveValue('previous input');
  await input(page).press('ArrowDown'); await expect(input(page)).toHaveValue('keep this draft');
});

test('covered chat stays unread; search highlights literal matches and reveals their context', async ({ page }) => {
  await ready(page);
  await page.getByRole('button',{name:'Help and commands'}).click();
  const before = await page.evaluate(() => (window as any).fixture.requests.filter((r:any)=>r.kind==='mark_read').length);
  await page.evaluate(() => (window as any).fixture.receive('literal [.*] target'));
  await expect(page.getByRole('dialog',{name:'Commands'})).toBeVisible();
  await page.waitForTimeout(350);
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r:any)=>r.kind==='mark_read').length)).toBe(before);
  await page.getByLabel('Find a command',{exact:true}).fill('find');
  await expect(page.locator('.commands li')).toHaveCount(1);
  await page.keyboard.press('Escape');
  await command(page,'/find [.*]');
  await expect(page.locator('.search mark')).toHaveText('[.*]');
  await page.getByRole('button',{name:'Show in conversation'}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.locator('.message.focused')).toContainText('literal [.*] target');
});

test('notification invitation stays quiet and read-only input cannot be sent', async ({ page }) => {
  await page.goto('/?device-unlock&notifications');
  await page.getByLabel('Identity passphrase',{exact:true}).fill('fixture-passphrase');
  await page.getByRole('button',{name:'Reconnect',exact:true}).click();
  await expect(page.locator('.notification-offer')).toBeVisible();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button',{name:'Enable background notifications…'}).click();
  await expect(page.getByRole('dialog',{name:'Notifications'})).toBeVisible(); await page.keyboard.press('Escape');
  await page.locator('.channels').getByRole('button',{name:/archive/}).click();
  await expect(page.locator('.composer-context')).toContainText('Read-only');
  await input(page).fill('keep this unsent'); await expect(page.getByRole('button',{name:'Send',exact:true})).toBeDisabled();
  await input(page).press('Enter'); await expect(input(page)).toHaveValue('keep this unsent');
  expect(await page.evaluate(() => (window as any).fixture.requests.some((r:any)=>r.kind==='submit' && r.text==='keep this unsent'))).toBe(false);
});

for (const width of [320,390,768,1100,1440]) test(`long Unicode content and both fonts fit ${width}px and short windows`, async ({ page }) => {
  await page.setViewportSize({ width,height:720 }); await ready(page);
  await page.evaluate(() => {
    const f=(window as any).fixture;
    f.setTopic('Long channel topic '.repeat(30));
    f.setMembers([{id:'self',nickname:'Iggy',isSelf:true,capabilities:[]},{id:'long',nickname:'VeryLongNickname'.repeat(12),isSelf:false,capabilities:[]}]);
    f.receive('https://example.test/'+'x'.repeat(400)+'\n  preserved spaces\n日本語 👋 مرحبا');
  });
  await expect(page.getByRole('log')).toContainText('日本語'); await noOverflow(page);
  await page.screenshot({ path:test.info().outputPath(`fixedsys-${width}.png`) });
  await command(page,'/font readable'); await noOverflow(page);
  await page.setViewportSize({width,height:320});
  await input(page).fill('first line\nsecond line\nthird line');
  const composer = await page.locator('.composer').boundingBox(); expect(composer!.y+composer!.height).toBeLessThanOrEqual(320);
  await noOverflow(page); await page.screenshot({ path:test.info().outputPath(`readable-short-${width}.png`) });
});
