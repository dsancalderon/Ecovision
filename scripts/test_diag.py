import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        
        page.on("console", lambda msg: print("[CONSOLE]", msg.type, msg.text))
        page.on("pageerror", lambda err: print("[PAGEERROR]", err))
        page.on("requestfailed", lambda req: print("[REQUEST FAILED]", req.url, req.failure))
        
        print("Navigating to workspace...")
        await page.goto("http://127.0.0.1:57803/workspace")
        await page.wait_for_timeout(1000)
        
        media = await page.evaluate("window.ECOVISION_MEDIA")
        print("window.ECOVISION_MEDIA in page:", media)
        
        print("Triggering lata_aluminio directly via App.transitionToState...")
        await page.evaluate("""() => {
            App.transitionToState(3, { class_name: 'lata_aluminio', confidence: 0.95 });
        }""")
        
        await page.wait_for_timeout(3000)
        
        state_info = await page.evaluate("""() => {
            const v = document.querySelector('#material-video');
            const stage = document.querySelector('#material-stage');
            const poster = document.querySelector('#material-poster');
            return {
                currentState: window.App ? window.App.currentState : null,
                videoSrc: v ? v.src : null,
                videoCurrentTime: v ? v.currentTime : null,
                videoPaused: v ? v.paused : null,
                videoHidden: v ? v.hidden : null,
                videoReadyState: v ? v.readyState : null,
                videoError: v && v.error ? { code: v.error.code, message: v.error.message } : null,
                stageClasses: stage ? stage.className : null,
                posterSrc: poster ? poster.src : null,
                posterHidden: poster ? poster.hidden : null
            };
        }""")
        print("State info:", state_info)
        
        await page.screenshot(path="verification/diag_lata.png")
        print("Screenshot saved to verification/diag_lata.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
