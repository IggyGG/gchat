import { test, expect, type Page } from '@playwright/test';
import { showUsers } from './navigation';

async function populate(page: Page) {
  await page.evaluate(() => {
    const f=(window as any).fixture, now=Math.floor(Date.now()/1000);
    const members=[{id:'self',nickname:'Iggy',isSelf:true,capabilities:['channel.owner']},{id:'ada',nickname:'Ada',isSelf:false,capabilities:[]},{id:'mira',nickname:'Mira',isSelf:false,capabilities:[]}];
    f.setMembers(members);
    f.setMessages([
      {id:'v1',nickname:'Ada',body:'Anyone around for a quick review?',mine:false,timestamp:now-120},
      {id:'v2',nickname:'Iggy',body:'Yep. Keeping the conversation easy to follow.',mine:true,timestamp:now-115,delivery:'delivered'},
      {id:'v3',nickname:'Mira',body:'The channel list feels familiar now.\n  Even pasted lines keep their spacing.',mine:false,timestamp:now-110},
      {id:'v4',nickname:'Ada',body:'@Iggy: can you check the files too?',mine:false,timestamp:now-80},
      {id:'v5',nickname:'Mira',body:'日本語 · مرحبا · a little Unicode 👋',mine:false,timestamp:now-60},
    ].map(message=>({conversationId:'channel/general',memberId:message.mine?'self':message.nickname.toLowerCase(),delivery:null,result:null,...message})));
    f.setActivity(Array.from({length:12},(_,index)=>({id:'visual-join-'+index,conversation:'channel/general',kind:'join',text:`guest${index} (${'a'.repeat(64)}) joined`,timestamp:now-100+index})));
  });
  await expect(page.getByRole('log')).toContainText('a little Unicode');
}

for (const width of [320,390,768,1100,1440]) test(`visual review of conversation, help, files and connection at ${width}px`, async ({page},info) => {
  const errors:string[]=[]; page.on('pageerror',error=>errors.push(error.message));
  await page.setViewportSize({width,height:800}); await page.goto('/'); await populate(page);
  await expect(page.locator('.activity')).toHaveCount(1);
  await page.screenshot({path:info.outputPath('conversation.png')});
  await page.getByRole('button',{name:'Files: 1',exact:true}).click();
  await expect(page.getByRole('dialog',{name:'Files',exact:true})).toContainText('4.0 KiB');
  await page.screenshot({path:info.outputPath('files.png')});
  await page.keyboard.press('Escape');
  await page.getByRole('button',{name:'Help and commands'}).click();
  await expect(page.getByLabel('Find a command')).toBeVisible();
  await page.screenshot({path:info.outputPath('help.png')});
  await page.keyboard.press('Escape');
  await page.evaluate(()=>(window as any).fixture.setNetwork('reconnecting'));
  await expect(page.locator('.connection-label')).toHaveText('Reconnecting');
  await page.screenshot({path:info.outputPath('reconnecting.png')});
  await showUsers(page);
  await page.screenshot({path:info.outputPath('users.png')});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});

test('new mentions in another channel remain visible without marking that channel read', async ({page})=>{
  await page.goto('/'); await expect(page.locator('.active-title')).toHaveText('#general');
  await page.evaluate(()=>(window as any).fixture.setMessages([{id:'design-mention',conversationId:'channel/design',memberId:'peer',nickname:'Ada',body:'@Iggy, please look here',timestamp:1900000000,mine:false,delivery:null,result:null}]));
  // A real snapshot changes the last-message identity. The fixture exposes it explicitly.
  await page.evaluate(()=>(window as any).fixture.setUnread('channel/design',2,'design-mention'));
  await expect(page.locator('.channel-entries button').filter({hasText:'design'}).getByLabel('Unread mention or highlight')).toBeVisible();
  expect(await page.evaluate(()=>(window as any).fixture.requests.some((r:any)=>r.kind==='mark_read'&&r.conversation==='channel/design'))).toBe(false);
});

test('font fallback and 200 percent zoom retain usable navigation and composer', async ({page},info)=>{
  await page.route('**/fonts/**',route=>route.abort());
  await page.setViewportSize({width:768,height:800}); await page.goto('/'); await populate(page);
  await page.evaluate(()=>document.documentElement.style.zoom='2');
  await expect(page.getByRole('textbox',{name:'Message or command'})).toBeVisible();
  await expect.poll(()=>page.locator('.composer').evaluate(el=>el.getBoundingClientRect().bottom)).toBeLessThanOrEqual(800);
  await page.getByRole('button',{name:'Help and commands'}).click();
  await expect(page.getByLabel('Find a command')).toBeVisible();
  const back = page.getByRole('button',{name:'Close dialog',exact:true});
  await expect(back).toBeInViewport({ratio:1});
  await expect(page.getByLabel('Find a command')).toBeInViewport({ratio:1});
  await page.screenshot({path:info.outputPath('fallback-zoom.png')});
  await page.keyboard.press('Escape');
  await expect(page.getByRole('log')).toContainText('a little Unicode');
});

test('text zoom collapses wide rails and keeps both composer and dialog header on screen', async ({page})=>{
  await page.setViewportSize({width:1100,height:800}); await page.goto('/');
  await expect(page.locator('#channel-navigation')).toBeVisible();
  await page.evaluate(()=>document.documentElement.style.zoom='2');
  await expect(page.locator('#channel-navigation')).toBeHidden();
  await expect.poll(()=>page.locator('.composer').evaluate(el=>el.getBoundingClientRect().bottom)).toBeLessThanOrEqual(800);
  await page.getByRole('button',{name:'Help and commands'}).click();
  await expect(page.getByRole('button',{name:'Close dialog'})).toBeInViewport({ratio:1});
  await page.getByLabel('Find a command').fill('font');
  await expect(page.locator('.commands li')).toHaveCount(1);
});

test('all IRC color pairs, inverse mentions and invalid-foreground resets remain readable', async ({page},info)=>{
  await page.goto('/'); await expect(page.locator('.active-title')).toHaveText('#general');
  await page.evaluate(()=>{
    let body='';
    for(let background=0;background<16;background++) for(let foreground=0;foreground<16;foreground++) body+=`\x03${String(foreground).padStart(2,'0')},${String(background).padStart(2,'0')} ${foreground}/${background} \x0f `;
    (window as any).fixture.receive(body+'\n\x16@Iggy\x0f \x0399,00default text on white');
  });
  const colors=page.locator('.message .colored'); await expect(colors).toHaveCount(258);
  const minimum=await colors.evaluateAll(nodes=>{
    const light=(color:string)=>{
      const channels=color.match(/[\d.]+/g)!.slice(0,3).map(n=>Number(n)/255).map(n=>n<=0.04045?n/12.92:((n+0.055)/1.055)**2.4);
      return channels[0]*0.2126+channels[1]*0.7152+channels[2]*0.0722;
    };
    return Math.min(...nodes.map(node=>{const style=getComputedStyle(node);const a=light(style.color),b=light(style.backgroundColor);return (Math.max(a,b)+0.05)/(Math.min(a,b)+0.05);}));
  });
  expect(minimum).toBeGreaterThanOrEqual(4.5);
  const mention=page.locator('.colored .mention');
  expect(await mention.evaluate(el=>getComputedStyle(el).color)).toBe(await mention.evaluate(el=>getComputedStyle(el.parentElement!).color));
  await page.screenshot({path:info.outputPath('irc-colors.png')});
});
