import { test, expect } from '@playwright/test';
const input = (page: import('@playwright/test').Page) => page.getByRole('textbox', {name:'Message or command'});
async function openUpdates(page: import('@playwright/test').Page) {
  await input(page).fill('/update'); await input(page).press('Enter');
  await expect(page.getByRole('heading',{name:'Application updates'})).toBeVisible();
}
test('restart is guarded by an unsent draft in another conversation', async({page})=>{
  await page.goto('/?native-shell&updates');
  await page.getByRole('button',{name:'Channels',exact:true}).click();
  await page.locator('#channel-navigation .channel-entries button').filter({has:page.locator('.room-name',{hasText:'general'})}).click();
  await input(page).fill('Keep my unsent draft');
  await page.getByRole('button',{name:'Channels',exact:true}).click();
  await page.locator('#channel-navigation .channel-entries button').filter({has:page.locator('.room-name',{hasText:'design'})}).click();
  await openUpdates(page);
  await expect(page.getByRole('button',{name:'Restart now'})).toBeDisabled();
  await expect(page.getByText('Finish or save your draft and wait for current actions before restarting.')).toBeVisible();
});
test('verified ready update has an explicit restart action', async({page})=>{
  await page.goto('/?native-shell&updates'); await openUpdates(page);
  await expect(page.getByRole('button',{name:'Restart now'})).toBeEnabled();
  await page.getByRole('button',{name:'Restart now'}).click();
  await expect.poll(()=>page.evaluate(()=> (window as any).fixture.updateRestarts())).toBe(1);
});
test('download progress and store-managed updates are visible',async({page})=>{
  await page.goto('/?native-shell&updates');
  await page.evaluate(()=> (window as any).fixture.setUpdate({state:'downloading',downloaded:256,total:1024,message:'Downloading update…'}));
  await openUpdates(page);
  await expect(page.getByRole('progressbar',{name:'Update download'})).toHaveAttribute('value','256');
  await expect(page.getByRole('button',{name:'Restart now'})).toHaveCount(0);
  await page.goto('/'); await openUpdates(page);
  await expect(page.getByText('This device uses its app store or installation provider for updates. Enable automatic updates there.')).toBeVisible();
});
