/** 
 * EcoVision — Local Video & Material Media Controller
 * Gestor robusto de reproducción de videos locales para cada material clasificado.
 * Compatible con políticas de Autoplay, WebView2, y fallback automático a póster/SVG.
 */
(() => {
    const stage = document.getElementById('material-stage');
    const host = document.getElementById('material-media');
    const video = document.getElementById('material-video');
    const poster = document.getElementById('material-poster');

    // El backend registra únicamente archivos que existen. Los demás usan SVG.
    const MEDIA = Object.freeze(window.ECOVISION_MEDIA || {});

    let active = false;
    let failed = false;
    let selected = '';
    let generation = 0;
    let pageVisible = true;
    let playPending = false;

    const shouldPlay = () => active && pageVisible && !document.hidden && !failed && Boolean(MEDIA[selected]);

    function releaseVideo() {
        if (!video) return;
        try {
            video.pause();
            video.currentTime = 0;
        } catch (_) {}
        video.hidden = true;
        video.removeAttribute('src');
        video.load();
        if (stage) stage.classList.remove('has-video');
        playPending = false;
    }

    function play() {
        if (!video || !shouldPlay() || playPending) return;
        const request = generation;
        const media = MEDIA[selected];
        if (!media) return;

        // Configuración estricta previa para garantizar compatibilidad con Autoplay de Chromium / WebKit
        video.muted = true;
        video.defaultMuted = true;
        video.setAttribute('muted', '');
        video.playsInline = true;
        video.setAttribute('playsinline', '');
        video.loop = true;

        const targetSrc = media.src;
        // Asignar src solo si cambió para evitar reloads y cancelaciones innecesarias
        if (video.getAttribute('src') !== targetSrc) {
            video.src = targetSrc;
            video.load();
        }

        playPending = true;
        const playPromise = video.play();

        if (playPromise !== undefined) {
            playPromise.then(() => {
                if (request === generation && shouldPlay()) {
                    video.hidden = false;
                    if (stage) stage.classList.add('has-video');
                }
            }).catch(error => {
                if (request !== generation) return;
                
                if (error.name === 'NotAllowedError') {
                    // Reintento garantizado silenciado si el navegador objetó por política de audio
                    video.muted = true;
                    video.defaultMuted = true;
                    video.play().then(() => {
                        if (request === generation && shouldPlay()) {
                            video.hidden = false;
                            if (stage) stage.classList.add('has-video');
                        }
                    }).catch(retryErr => {
                        console.warn(`[EcoVision Video] Autoplay restringido para '${selected}'. Manteniendo póster/SVG:`, retryErr.message);
                        failed = true;
                        releaseVideo();
                    });
                } else if (error.name !== 'AbortError') {
                    console.warn(`[EcoVision Video] Fallo al iniciar video para '${selected}':`, error.message);
                    failed = true;
                    releaseVideo();
                }
            }).finally(() => {
                if (request === generation) playPending = false;
            });
        }
    }

    function refresh() {
        if (!shouldPlay()) {
            generation++;
            playPending = false;
            if (video) video.pause();
        } else {
            play();
        }
    }

    if (video) {
        video.addEventListener('playing', () => {
            if (shouldPlay()) {
                video.hidden = false;
                if (stage) stage.classList.add('has-video');
            } else {
                video.pause();
            }
        });

        video.addEventListener('canplay', () => {
            if (shouldPlay() && !video.paused) {
                video.hidden = false;
                if (stage) stage.classList.add('has-video');
            }
        });

        video.addEventListener('timeupdate', () => {
            if (shouldPlay() && video.currentTime > 0.05 && !video.paused) {
                video.hidden = false;
                if (stage) stage.classList.add('has-video');
            }
        });

        video.addEventListener('error', () => {
            const currentSrc = video.getAttribute('src');
            if (!currentSrc) return;
            console.warn(`[EcoVision Video] Archivo no disponible o códec no soportado (${currentSrc}). Usando vista de respaldo.`);
            failed = true;
            releaseVideo();
        });
    }

    // El clip se prepara al comenzar un análisis; el menú no descarga videos.
    if (video) {
        video.muted = true;
        video.defaultMuted = true;
        video.setAttribute('muted', '');
        video.playsInline = true;
        video.setAttribute('playsinline', '');
        video.preload = 'none';
    }

    if (poster) {
        poster.addEventListener('load', () => {
            if (active && MEDIA[selected]?.poster === poster.getAttribute('src')) {
                if (stage) stage.classList.add('has-poster');
            }
        });
        poster.addEventListener('error', () => {
            poster.hidden = true;
            if (stage) stage.classList.remove('has-poster');
        });
    }

    window.EcoMaterialMedia = {
        /**
         * Pre-carga y pre-calienta el clip en segundo plano durante el escaneo (Estado 2)
         * para que arranque en t=0ms sin congelamiento ni retraso al pasar a Estado 3.
         */
        prepare(key) {
            const media = MEDIA[key];
            if (!media || !video) return;

            video.muted = true;
            video.defaultMuted = true;
            video.setAttribute('muted', '');
            video.playsInline = true;
            video.setAttribute('playsinline', '');
            video.preload = 'auto';

            const targetSrc = media.src;
            if (video.getAttribute('src') !== targetSrc) {
                video.src = targetSrc;
            }
        },

        show(key, name) {
            generation++;
            active = true;
            selected = key;
            failed = false;

            if (stage) {
                stage.classList.remove('has-poster');
                stage.classList.remove('has-video');
                stage.hidden = false;
                stage.dataset.material = key;
            }

            if (host) {
                host.setAttribute('aria-label', `Vista de ${name}`);
            }

            // Fallbacks vectoriales SVG (se muestran si no hay video/póster o mientras carga)
            if (stage) {
                stage.querySelectorAll('[data-material-fallback]').forEach(svg => {
                    svg.toggleAttribute('hidden', svg.dataset.materialFallback !== key);
                });
            }

            const media = MEDIA[key];
            if (poster) {
                poster.hidden = !media?.poster;
                if (media?.poster) {
                    poster.src = media.poster;
                } else {
                    poster.removeAttribute('src');
                }
            }

            if (media) {
                this.prepare(key);
                play();
            } else {
                releaseVideo();
            }
        },

        hide() {
            generation++;
            active = false;
            if (stage) stage.hidden = true;
            releaseVideo();
            if (poster) {
                poster.hidden = true;
                poster.removeAttribute('src');
            }
        }
    };

    // Control de visibilidad del documento (pausar si la pestaña se oculta)
    document.addEventListener('visibilitychange', () => {
        pageVisible = !document.hidden;
        refresh();
    });
    window.addEventListener('pagehide', () => {
        pageVisible = false;
        generation++;
        releaseVideo();
    });
    window.addEventListener('pageshow', () => {
        pageVisible = true;
        refresh();
    });
})();
