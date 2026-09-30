import { test, expect } from '@playwright/test';
for (const width of [390, 1100]) test(`owner recovery confirms explicit selection at ${width}px`, async ({ page }) => {
  await page.setViewportSize({width,height:720});
  await page.goto('/');
  await page.getByRole('button', {name: /Users/}).first().click();
  await page.getByRole('button', {name:'Channel recovery…'}).click();
  await expect(page.getByRole('heading', {name:'Channel recovery · general'})).toBeVisible();
  await expect(page.getByText('Removing a member does not mark their messages delivered.', {exact:false})).toBeVisible();
  await expect(page.getByRole('checkbox')).toHaveCount(1);
  await page.getByRole('checkbox').check();
  await page.getByRole('button', {name:'Remove selected members…'}).click();
  await expect(page.getByRole('button', {name:'Confirm removal'})).toBeVisible();
  await page.screenshot({path:test.info().outputPath('recovery-confirmation.png'),fullPage:true});
  await page.getByRole('button', {name:'Cancel',exact:true}).click();
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r:any)=>r.kind==='submit' && r.text.startsWith('/recover-membership ')).length)).toBe(0);
  await page.getByRole('button', {name:'Remove selected members…'}).click();
  await page.getByRole('button', {name:'Confirm removal'}).click();
  await expect(page.getByText('You are the only member.', {exact:false})).toBeVisible();
  expect(await page.evaluate(() => (window as any).fixture.requests.filter((r:any)=>r.kind==='submit' && r.text.startsWith('/recover-membership ')).map((r:any)=>[r.conversation,r.text]))).toEqual([['channel/general','/recover-membership preview-token removed-leaf']]);
});
test('members do not see the owner recovery action', async ({page}) => {
  await page.goto('/?member');
  await page.getByRole('button', {name:/Users/}).first().click();
  await expect(page.getByRole('button', {name:'Channel recovery…'})).toHaveCount(0);
});

test('stale recovery is visible and never reported as successful removal', async ({page}) => {
  await page.goto('/?recovery-stale');
  await page.getByRole('button', {name:/Users/}).first().click();
  await page.getByRole('button', {name:'Channel recovery…'}).click();
  await page.getByRole('checkbox').check();
  await page.getByRole('button', {name:'Remove selected members…'}).click();
  await page.getByRole('button', {name:'Confirm removal'}).click();
  await expect(page.getByText('You are the only member.', {exact:false})).toHaveCount(0);
  await expect(page.getByText('Recovery was not confirmed.', {exact:false})).toBeVisible();
  await page.getByRole('button', {name:'Refresh preview'}).click();
  await expect(page.getByRole('checkbox')).toBeVisible();
});
