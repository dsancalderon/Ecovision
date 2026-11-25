/* Local desktop shell and development reload. No remote requests. */
const Desktop = {
    pending: false,
    async fitWindow() {
        if (!window.pywebview?.api?.layout) return;
        if (this.fitting) { this.fitAgain = true; return; }
        this.fitting = true;
        try {
            const home = document.querySelector('.home-shell');
            if (home) document.body.classList.add('native-desktop');
            const height = home ? Math.ceil(home.getBoundingClientRect().height) : 0;
            const state = await window.pywebview.api.layout(home ? 'home' : 'workspace', height, innerWidth, innerHeight);
            if (state.fullscreen) document.body.classList.remove('native-desktop');
        } finally {
            this.fitting = false;
            if (this.fitAgain) { this.fitAgain = false; this.fitWindow(); }
        }
    },
    async api(path, options = {}) {
        const response = await fetch(path, { ...options, signal: AbortSignal.timeout(60000) });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'No se pudo completar la operación.');
        return data;
    },
    async choose(mode) {
        if (this.pending) return;
        this.pending = true;
        this.loading('Preparando tu experiencia…', 10);
        try {
            await this.api('/api/mode', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode, camera_index: Number(document.querySelector('#camera-choice')?.value || 0) }) });
            await this.waitForMode(mode);
        } catch (error) { this.error(error.message); }
    },
    loading(message, value) {
        document.querySelector('#menu-panel')?.setAttribute('hidden', '');
        const panel = document.querySelector('#startup-panel');
        if (!panel) return;
        panel.hidden = false;
        document.querySelector('#loading-message').textContent = message;
        document.querySelector('#startup-progress').value = value;
        document.querySelector('#loading-error').hidden = true;
        document.querySelector('#back-from-error').hidden = true;
    },
    error(message) {
        const el = document.querySelector('#loading-error');
        if (!el) return;
        el.textContent = message; el.hidden = false;
        document.querySelector('#loading-title').textContent = 'Necesitamos revisar un detalle.';
        document.querySelector('#back-from-error').hidden = false;
        this.pending = false;
        this.fitWindow();
    },
    showMenu() {
        document.querySelector('#startup-panel').hidden = true;
        document.querySelector('#menu-panel').hidden = false;
        document.querySelector('#loading-title').textContent = 'Preparando una mejor decisión.';
        this.pending = false;
        this.fitWindow();
    },
    async waitForMode(mode) {
        const started = Date.now();
        while (Date.now() - started < 120000) {
            const status = await this.api('/api/session');
            this.loading(status.message, status.progress);
            if (status.phase === 'error') throw new Error(status.error);
            if (status.phase === 'ready') {
                if (mode === 'menu') this.showMenu();
                else location.assign('/workspace');
                return;
            }
            await new Promise(resolve => setTimeout(resolve, 250));
        }
        throw new Error('La preparación está tardando más de lo esperado. Espera antes de reintentar.');
    },
    async menu() {
        const button = document.querySelector('#return-menu');
        if (button) button.disabled = true;
        try {
            if (typeof App !== 'undefined') {
                App.stopFallbackPolling();
                App.eventSource?.close();
                App.transitionToState(1);
            }
            document.body.dataset.interfaceOnly = 'true';
            const feed = document.querySelector('#main-video-feed');
            if (feed) { feed.onerror = null; feed.removeAttribute('src'); }
            await this.api('/api/mode', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: 'menu' }) });
            location.assign('/');
        } catch (error) {
            this.alert(error.message); if (button) button.disabled = false;
        }
    },
    alert(message) {
        let el = document.querySelector('.session-alert');
        if (!el) { el = document.createElement('div'); el.className = 'session-alert'; el.setAttribute('role', 'alert'); document.body.append(el); }
        el.textContent = message;
    },
    async watchDevelopment(initialRevision) {
        let baseline = initialRevision;
        this.watchTimer = setInterval(async () => {
            if (this.checking) return;
            this.checking = true;
            try {
                const data = await this.api('/api/session');
                if (baseline && baseline !== data.ui_revision) location.reload();
                baseline = data.ui_revision;
            } catch (_) { /* Backend restarts reopen the desktop window. */ }
            finally { this.checking = false; }
        }, 1500);
    },
    async init() {
        document.querySelector('#choose-simulation')?.addEventListener('click', () => this.choose('simulation'));
        document.querySelector('#choose-real')?.addEventListener('click', () => this.choose('real'));
        document.querySelector('#back-from-error')?.addEventListener('click', () => this.choose('menu'));
        document.querySelector('#return-menu')?.addEventListener('click', () => this.menu());
        document.querySelector('#reload-ui')?.addEventListener('click', () => location.reload());
        document.querySelector('#restart-engine')?.addEventListener('click', async () => {
            if (window.pywebview?.api) await window.pywebview.api.restart();
            else this.alert('El reinicio del motor está disponible en la ventana de escritorio de desarrollo.');
        });
        try {
            const data = await this.api('/api/session');
            if (!document.querySelector('#menu-panel')) await this.fitWindow();
            if (data.development) this.watchDevelopment(document.body.dataset.uiRevision || data.ui_revision);
            if (!document.querySelector('#menu-panel')) return;
            this.loading('Verificando imágenes y tipografías locales…', 45);
            await Promise.all([document.fonts.ready, ...Array.from(document.images).map(img => img.decode().catch(() => {}))]);
            const choice = document.querySelector('#camera-choice');
            const cameraData = await this.api('/api/cameras');
            choice.replaceChildren();
            for (const camera of cameraData.cameras) {
                choice.add(new Option(camera.name, camera.index));
            }
            if (cameraData.cameras.length) {
                choice.disabled = false;
                document.querySelector('#choose-real').disabled = false;
                if (choice.querySelector(`option[value="${data.camera_index}"]`)) choice.value = data.camera_index;
            } else {
                choice.add(new Option(cameraData.error || 'Sin cámaras disponibles', ''));
            }
            if (data.phase === 'loading') await this.waitForMode(data.mode);
            else if (data.phase === 'ready' && data.mode !== 'menu') location.replace('/workspace');
            else this.showMenu();
        } catch (error) { this.error(error.message); }
    }
};
document.addEventListener('DOMContentLoaded', () => Desktop.init());
window.addEventListener('pywebviewready', () => {
    window.pywebview?.api?.ready?.();
    Desktop.fitWindow();
});
window.addEventListener('pagehide', () => clearInterval(Desktop.watchTimer));
document.addEventListener('keydown', event => {
    if (document.body.classList.contains('desktop-home') &&
        (event.key === 'F11' || (event.altKey && event.key === 'Enter'))) {
        event.preventDefault();
        event.stopImmediatePropagation();
    }
}, true);
