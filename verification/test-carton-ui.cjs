const { chromium } = require('playwright');
const path = require('path');

(async () => {
    const browser = await chromium.launch({ channel: 'msedge', headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 850 } });
    const page = await context.newPage();

    const filePath = 'file:///' + path.resolve('verification/video-preview.html').replace(/\\/g, '/');
    await page.goto(filePath, { waitUntil: 'domcontentloaded' });

    await page.evaluate(() => {
        const stage = document.querySelector('#material-stage');
        const video = document.querySelector('#material-video');
        const poster = document.querySelector('#material-poster');
        
        stage.dataset.material = 'papel_carton';
        video.src = '../static/videos/papel_carton.mp4';
        video.currentTime = 1.0;
        video.hidden = false;
        if (poster) poster.src = '../static/videos/papel_carton-poster.jpg';

        // Update labels
        document.querySelector('.result-material-type').textContent = 'PAPEL Y CARTÓN LIMPIO';
        document.querySelector('.result-material-title').textContent = 'Caja de Cartón';
        document.querySelector('.result-material-desc').textContent = 'Cartón corrugado 100% reciclable. Desarma y aplana la caja para optimizar espacio.';
        document.querySelector('.badge-conf').textContent = 'Confianza IA: 94%';
    });

    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'verification/video-carton-desktop.png' });
    console.log('Screenshot saved to verification/video-carton-desktop.png');
    await browser.close();
})();
