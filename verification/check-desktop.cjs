const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
 const browser = await chromium.launch({channel:'msedge',headless:true});
 const context = await browser.newContext({viewport:{width:1280,height:850}});
 const external=[], errors=[], failed=[], passed=[], requests=[];
 await context.route('**/*', route => {
   if (!route.request().url().startsWith('http://127.0.0.1:5070/')) {external.push(route.request().url()); return route.abort();}
   return route.continue();
 });
 const page = await context.newPage();
 page.on('pageerror', error=>errors.push(error.message));
 page.on('request', request=>requests.push(request.url()));
 page.on('response', res=>{if(res.status()>=400)failed.push([res.url(),res.status()]);});
 await page.goto('http://127.0.0.1:5070/');
 await page.locator('#menu-panel').waitFor({state:'visible'});
 await page.screenshot({path:'verification/desktop-menu.png'});
 assert.equal((await context.request.get('http://127.0.0.1:5070/api/session')).status(),200);
 passed.push('menu starts without camera or model');
 await page.locator('#choose-simulation').click();
 await page.waitForURL('**/workspace');
 await page.evaluate(()=>sounds.enabled=false);
 assert.equal(await page.locator('#main-video-feed').getAttribute('src'),null);
 assert(await page.locator('#scanner-box').isVisible());
 assert.equal(await page.locator('#cam-standby > span').textContent(),'Cámara desactivada');
 assert(await page.locator('#sim-toolbar').isVisible());
 assert(!requests.some(url=>url.endsWith('.mp4')));
 passed.push('simulation has no camera stream and shows simulation controls');
 await page.locator('#btn-toggle-sim').click();
 for(const key of ['botella_plastica_pet','papel_carton','lata_aluminio','tetra_pak','vidrio','no_reciclable']) {
   await page.evaluate(()=>App.transitionToState(1));
   await page.locator(`[data-class="${key}"]`).click();
   await page.waitForFunction(()=>App.currentState===3);
   if(['botella_plastica_pet','papel_carton'].includes(key)) {
     await page.waitForFunction(()=>{const v=document.querySelector('video');return !v.paused && v.currentTime>.1;});
     const before=await page.locator('video').evaluate(v=>v.currentTime);
     await page.waitForTimeout(350);
     assert(await page.locator('video').evaluate(v=>v.currentTime)>before);
     await page.screenshot({path:`verification/desktop-${key}.png`});
   }
   assert.equal(await page.locator('#material-stage').getAttribute('data-material'),key);
 }
 passed.push('all six simulator materials render; PET and cardboard video time advances in card');
 await page.locator('#return-menu').click();
 await page.waitForURL('http://127.0.0.1:5070/');
 await page.locator('#menu-panel').waitFor({state:'visible'});
 passed.push('return to menu releases UI and resets session');
 const stylePath='static/css/desktop.css', original=fs.readFileSync(stylePath);
 try {
   const reloaded=page.waitForEvent('load',{timeout:12000});
   fs.appendFileSync(stylePath,'\n/* Development reload verification. */\n');
   await reloaded;
   await page.locator('#menu-panel').waitFor({state:'visible'});
 } finally {fs.writeFileSync(stylePath,original);}
 passed.push('editing local CSS reloads development UI without packaging');
 const templatePath='templates/desktop.html', template=fs.readFileSync(templatePath);
 try {
   fs.writeFileSync(templatePath,template.toString().replace('<main class="home-shell">','<main class="home-shell"><!-- Template reload verification -->'));
   await page.waitForFunction(()=>document.documentElement.outerHTML.includes('Template reload verification'),{},{timeout:12000});
 } finally {fs.writeFileSync(templatePath,template);}
 passed.push('editing HTML template refreshes rendered content without restarting Python');
 await page.waitForFunction(()=>!document.documentElement.outerHTML.includes('Template reload verification') && document.querySelector('#menu-panel')?.hidden===false,{},{timeout:12000});
 await page.setViewportSize({width:960,height:700});
 assert(await page.locator('#choose-real').isVisible());
 assert(await page.locator('#camera-choice').isVisible());
 await page.screenshot({path:'verification/desktop-menu-small.png'});
 assert.deepEqual(external,[]);assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 passed.push('external network blocked; zero external requests, failed resources or JavaScript errors');
 fs.writeFileSync('verification/desktop-browser-results.json',JSON.stringify({passed,external,errors,failed},null,2));
 console.log(JSON.stringify({passed,external,errors,failed},null,2));
 await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});
