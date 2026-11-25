import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        
        page.on("console", lambda msg: print(f"[{msg.type.upper()}] {msg.text}"))
        page.on("pageerror", lambda err: print("[PAGEERROR]", err))
        
        await page.goto("http://127.0.0.1:57803/workspace")
        await page.wait_for_timeout(500)
        
        # Open drawer
        print("Toggling sim drawer...")
        await page.locator('#btn-toggle-sim').click()
        await page.wait_for_timeout(300)
        
        # Click lata_aluminio
        print("Clicking lata_aluminio chip...")
        chip = page.locator('.sim-chip[data-class="lata_aluminio"]')
        await chip.click()
        
        # Step through: state 2 scanning
        print("Waiting 1s (scanning state)...")
        await page.wait_for_timeout(1000)
        
        # State 3 result
        print("Waiting 1s (result state)...")
        await page.wait_for_timeout(1000)
        
        info = await page.evaluate("""() => {
            const v = document.querySelector('#material-video');
            const poster = document.querySelector('#material-poster');
            const stage = document.querySelector('#material-stage');
            const modal = document.querySelector('#result-modal');
            const fallback = document.querySelector('[data-material-fallback="lata_aluminio"]');
            return {
                modalActive: modal.classList.contains('active'),
                stageHasVideo: stage.classList.contains('has-video'),
                stageHasPoster: stage.classList.contains('has-poster'),
                videoPaused: v.paused,
                videoCurrentTime: v.currentTime,
                videoSrc: v.src,
                videoHidden: v.hidden,
                fallbackHidden: fallback.hasAttribute('hidden'),
                fallbackVisible: fallback.offsetParent !== null
            };
        }""")
        print("Simulation result info:", info)
        await page.screenshot(path="verification/diag_sim_click.png")
        print("Saved verification/diag_sim_click.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
