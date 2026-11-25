// Run with Playwright available in NODE_PATH and Flask at http://127.0.0.1:5055.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1280,height:850}});
 const page=await context.newPage();
 const errors=[],requests=[],passed=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
 await page.addInitScript(()=>{
  const original=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(type,...args){if(type.startsWith('webgl'))throw new Error('Unexpected graphics engine');return original.call(this,type,...args);};
 });
 await page.goto('http://127.0.0.1:5055',{waitUntil:'domcontentloaded'});
 await page.evaluate(()=>sounds.enabled=false);
 assert.equal(requests.filter(url=>url.endsWith('.mp4')).length,0);
 assert.equal(await page.locator('canvas').count(),0);
 assert.equal(await page.locator('video').count(),1);
 assert(!requests.some(url=>/three|material-models|bottle-viewer/.test(url)));
 passed.push('idle: no video download, canvas or graphics engine; one video element');
 const show=async(key,freeze=true)=>{
  await page.evaluate(({key,freeze})=>{App.transitionToState(3,{class_name:key,confidence:.97});if(freeze){clearTimeout(App.resultTimeout);clearInterval(App.countdownInterval);}},{key,freeze});
 };
 const playing=()=>page.waitForFunction(()=>{const v=document.querySelector('#material-video');return !v.paused&&v.currentTime>.15&&!v.hidden;});
 await page.locator('#btn-toggle-sim').click();
 await page.locator('[data-class="botella_plastica_pet"]').click();
 await page.waitForFunction(()=>App.currentState===3);await playing();
 await page.evaluate(()=>{clearTimeout(App.resultTimeout);clearInterval(App.countdownInterval);});
 await page.locator('#btn-toggle-sim').click();
 const meta=await page.locator('video').evaluate(v=>({width:v.videoWidth,height:v.videoHeight,duration:v.duration,muted:v.muted,controls:v.controls,loop:v.loop,rate:v.playbackRate}));
 assert.equal(meta.width,720);assert.equal(meta.height,1280);assert.equal(meta.muted,true);assert.equal(meta.controls,false);assert.equal(meta.loop,true);assert.equal(meta.rate,1);
 const t0=await page.locator('video').evaluate(v=>v.currentTime);await page.waitForTimeout(500);
 assert(await page.locator('video').evaluate(v=>v.currentTime)>t0+.2);
 await page.screenshot({path:'verification/video-pet-desktop.png'});
 passed.push('PET simulator: actual MP4 decodes and advances, muted, looping, no controls');
 // Produce a standalone visual preview with the real layout, CSS and local video.
 const preview=await page.evaluate(()=>{
  const doc=document.documentElement.cloneNode(true);
  doc.querySelectorAll('script').forEach(el=>el.remove());
  doc.querySelectorAll('[onerror]').forEach(el=>el.removeAttribute('onerror'));
  doc.querySelectorAll('.sim-drawer, #btn-toggle-sim').forEach(el=>el.remove());
  doc.querySelectorAll('[src],[href]').forEach(el=>{
   for(const attr of ['src','href']){
    const value=el.getAttribute(attr);
    if(value?.startsWith('/static/'))el.setAttribute(attr,'../static/'+value.slice(8));
    if(value?.startsWith('/video_feed'))el.removeAttribute(attr);
   }
  });
  const v=doc.querySelector('video');v.setAttribute('autoplay','');v.setAttribute('muted','');v.removeAttribute('hidden');
  doc.querySelector('.result-timer-box').textContent='Vista previa · reproducción continua';
  return '<!doctype html>'+doc.outerHTML;
 });
 fs.writeFileSync('verification/video-preview.html',preview);
 // Every PET alias selects this same clip.
 for(const key of ['Botellas_reciclable','botella_reciclable','botella','bottle']){await show(key);await playing();assert.equal(await page.locator('#material-stage').getAttribute('data-material'),'botella_plastica_pet');}
 passed.push('all existing PET aliases select supplied clip');
 const staticKeys=['lata_aluminio','papel_carton','tetra_pak','vidrio','no_reciclable'];
 for(const key of staticKeys){
  await show(key);
  assert(await page.locator(`[data-material-fallback="${key}"]`).isVisible());
  assert.equal(await page.locator('video').getAttribute('src'),null);
  assert(await page.locator('video').evaluate(v=>v.paused));
 }
 await page.screenshot({path:'verification/video-static-fallback.png'});
 passed.push('five materials without supplied videos keep their individual SVG and no decoder source');
 await show('botella_plastica_pet');await playing();
 await page.evaluate(()=>App.transitionToState(1));
 assert.equal(await page.locator('video').getAttribute('src'),null);assert(await page.locator('#material-stage').isHidden());
 await page.waitForTimeout(350);assert(await page.locator('video').evaluate(v=>v.paused));
 passed.push('idle releases source and decoder');
 await show('botella_plastica_pet');await playing();
 await page.evaluate(()=>dispatchEvent(new Event('blur')));await page.waitForTimeout(150);
 let frozen=await page.locator('video').evaluate(v=>v.currentTime);await page.waitForTimeout(200);
 assert.equal(await page.locator('video').evaluate(v=>v.currentTime),frozen);
 await page.evaluate(()=>dispatchEvent(new Event('focus')));await playing();
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
 assert(await page.locator('video').evaluate(v=>v.paused));
 await page.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));});await playing();
 passed.push('blur/hidden document pause playback; focus/visibility resume');
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.waitForFunction(()=>!document.querySelector('video').hasAttribute('src'));
 assert.equal(await page.locator('video').getAttribute('src'),null);
 assert(await page.locator('#material-poster').isVisible());
 await show('botella_plastica_pet');assert.equal(await page.locator('video').getAttribute('src'),null);
 await page.emulateMedia({reducedMotion:'no-preference'});await playing();
 passed.push('reduced motion uses the video poster without loading the MP4');
 // Rapid replacements and reset must not resurrect an old video.
 await page.evaluate(()=>{for(const key of ['botella_plastica_pet','vidrio','botella_plastica_pet','no_reciclable'])App.transitionToState(3,{class_name:key,confidence:.9});App.transitionToState(1);});
 await page.waitForTimeout(300);assert.equal(await page.locator('video').getAttribute('src'),null);
 assert(await page.locator('video').evaluate(v=>v.paused));
 await show('botella_plastica_pet');await playing();
 await page.evaluate(()=>dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true})));
 assert.equal(await page.locator('video').getAttribute('src'),null);
 await page.evaluate(()=>dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})));await playing();
 passed.push('rapid class changes and page lifecycle release/restore playback');
 for(const width of [650,390]){
  await page.setViewportSize({width,height:850});await page.waitForTimeout(200);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:`verification/video-pet-${width}.png`});
 }
 passed.push('responsive result at 650px and 390px without horizontal overflow');
 await page.setViewportSize({width:1280,height:850});
 // Inject live detections through the camera event entry point, not a physical camera.
 await page.evaluate(()=>{App.transitionToState(1);window.detect=setInterval(()=>App.handleBackendUpdate({active_detection:{class_name:'Botellas_reciclable',confidence:.97},conf_threshold:.6}),80);});
 await page.waitForFunction(()=>App.currentState===3);await page.evaluate(()=>clearInterval(window.detect));await playing();
 await page.waitForFunction(()=>App.currentState===1,null,{timeout:7000});assert.equal(await page.locator('video').getAttribute('src'),null);
 await page.evaluate(()=>App.handleBackendUpdate({active_detection:{class_name:'bottle',confidence:.97},conf_threshold:.6}));await page.waitForTimeout(650);
 assert.equal(await page.evaluate(()=>App.currentState),1);
 passed.push('continuous detection path, 4.2s automatic reset and object withdrawal cancellation');
 // Real end-of-media loop, not just a loop attribute assertion.
 await show('botella_plastica_pet');await playing();
 await page.locator('video').evaluate(v=>v.currentTime=v.duration-.15);
 await page.waitForFunction(()=>{const v=document.querySelector('video');return !v.paused&&v.currentTime<1;});
 passed.push('playback loops at end of the full 10-second file');
 // Existing SSE correction remains effective.
 await page.evaluate(()=>{App.fallbackPolling();window.poll=App.pollingInterval;for(let i=0;i<10;i++)App.fallbackPolling();});
 assert(await page.evaluate(()=>window.poll===App.pollingInterval));await page.evaluate(()=>App.eventSource.onopen());assert(await page.evaluate(()=>!App.pollingInterval));
 passed.push('SSE fallback polling stays singleton and stops on reconnect');
 async function faultPage(setup,label){
  const p=await browser.newPage();p.on('pageerror',e=>errors.push(e.message));await setup(p);
  await p.goto('http://127.0.0.1:5055',{waitUntil:'domcontentloaded'});
  await p.evaluate(()=>{sounds.enabled=false;App.transitionToState(3,{class_name:'botella_plastica_pet',confidence:.97});});
  await p.waitForFunction(()=>{const p=document.querySelector('#material-poster');return p.complete&&p.naturalWidth>0;});
  assert(await p.locator('#material-poster').isVisible());
  await p.waitForFunction(()=>App.currentState===1,null,{timeout:7000});assert.equal(await p.locator('video').getAttribute('src'),null);
  await p.close();passed.push(label);
 }
 await faultPage(p=>p.route('**/*.mp4',r=>r.fulfill({status:404,body:'missing'})),'missing video: poster fallback and normal countdown');
 await faultPage(p=>p.addInitScript(()=>{HTMLMediaElement.prototype.play=function(){return Promise.reject(new DOMException('Blocked','NotAllowedError'));};}),'autoplay denied: poster fallback and normal countdown');
 const cold=await browser.newPage();cold.on('pageerror',e=>errors.push(e.message));
 let release;const gate=new Promise(resolve=>release=resolve);
 await cold.route('**/*.mp4',async r=>{await gate;try{await r.continue();}catch(_){}});
 await cold.goto('http://127.0.0.1:5055',{waitUntil:'domcontentloaded'});
 await cold.evaluate(()=>{sounds.enabled=false;App.transitionToState(3,{class_name:'bottle',confidence:.97});});
 assert(await cold.locator('#result-modal').isVisible());
 await cold.waitForFunction(()=>App.currentState===1,null,{timeout:7000});release();await cold.waitForTimeout(300);
 assert.equal(await cold.locator('video').getAttribute('src'),null);assert(await cold.locator('video').evaluate(v=>v.paused));
 passed.push('slow video load cannot block countdown or reopen a completed result');
 assert.deepEqual(errors,[]);
 const report={date:new Date().toISOString(),environment:'Headless Edge, Flask without physical camera',passed,video:meta,errors};
 fs.writeFileSync('verification/results.json',JSON.stringify(report,null,2));
 await browser.close();console.log(JSON.stringify(report,null,2));
})().catch(error=>{console.error(error);process.exit(1);});
