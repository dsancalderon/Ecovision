/**
 * EcoVision — Interactive Frontend Controller (Mockup Edition)
 * Manages Real-Time Center Camera, True Temporal Analysis Cooldown, Synthetic Web Audio & SSE Events
 */

// ==========================================================================
// 1. Material Classification Database
// ==========================================================================

const MATERIAL_DATABASE = {
    "botella_plastica_pet": {
        name: "Botella Plástica PET",
        category: "PLÁSTICO APROVECHABLE",
        isRecyclable: true,
        bin: "blanca",
        binName: "CANECA BLANCA",
        binDescription: "Residuos aprovechables limpios y secos",
        icon: "ph-fill ph-bottle",
        description: "Envase termoplástico 100% reciclable. Vacía los líquidos y aplástala para optimizar espacio.",
        ecoImpact: "+15 EcoPuntos • Ahorro de 0.08 kg CO₂"
    },
    "bottle": {
        name: "Botella Plástica (PET)",
        category: "PLÁSTICO APROVECHABLE",
        isRecyclable: true,
        bin: "blanca",
        binName: "CANECA BLANCA",
        binDescription: "Residuos aprovechables limpios y secos",
        icon: "ph-fill ph-bottle",
        description: "Envase termoplástico 100% reciclable. Vacía los líquidos y aplástala para optimizar espacio.",
        ecoImpact: "+15 EcoPuntos • Ahorro de 0.08 kg CO₂"
    },
    "lata_aluminio": {
        name: "Lata de Aluminio",
        category: "METAL APROVECHABLE",
        isRecyclable: true,
        bin: "blanca",
        binName: "CANECA BLANCA",
        binDescription: "Residuos aprovechables limpios y secos",
        icon: "ph-fill ph-brand-alipay",
        description: "Metal con ciclo de reciclaje infinito. Ahorra hasta un 95% de energía en su fundición.",
        ecoImpact: "+20 EcoPuntos • Ahorro de 0.15 kg CO₂"
    },
    "tetra_pak": {
        name: "Envase Tetra Pak",
        category: "MULTICAPA APROVECHABLE",
        isRecyclable: true,
        bin: "blanca",
        binName: "CANECA BLANCA",
        binDescription: "Residuos aprovechables limpios y secos",
        icon: "ph-fill ph-package",
        description: "Compuesto de cartón, polietileno y aluminio. Escúrrelo y déjalo plano antes de depositarlo.",
        ecoImpact: "+12 EcoPuntos • Ahorro de 0.06 kg CO₂"
    },
    "papel_carton": {
        name: "Papel o Cartón Limpio",
        category: "CELULOSA APROVECHABLE",
        isRecyclable: true,
        bin: "blanca",
        binName: "CANECA BLANCA",
        binDescription: "Residuos aprovechables limpios y secos",
        icon: "ph-fill ph-newspaper",
        description: "Hojas, cajas o empaques sin grasa ni humedad. Fácilmente reincorporable a la cadena de valor.",
        ecoImpact: "+10 EcoPuntos • Ahorro de 0.05 kg CO₂"
    },
    "vidrio": {
        name: "Envase de Vidrio",
        category: "VIDRIO APROVECHABLE",
        isRecyclable: true,
        bin: "blanca",
        binName: "CANECA BLANCA",
        binDescription: "Envases de vidrio limpios y vacíos",
        icon: "ph-fill ph-bottle",
        description: "Botellas y frascos de vidrio. Vacía el contenido y evita mezclar con cerámica, espejos o bombillos.",
        ecoImpact: "Recupera el material • Envases limpios y secos"
    },
    "no_reciclable": {
        name: "Residuo No Aprovechable",
        category: "NO RECICLABLE / ORDINARIO",
        isRecyclable: false,
        bin: "negra",
        binName: "CANECA NEGRA",
        binDescription: "Residuos no aprovechables ni reciclables",
        icon: "ph-fill ph-x-circle",
        description: "Servilletas sucias, papeles metalizados, restos de comida o empaques contaminados.",
        ecoImpact: "0 EcoPuntos • Disposición sanitaria segura"
    }
};

// ==========================================================================
// 2. Synthetic Audio Engine (Web Audio API)
// ==========================================================================

class SoundManager {
    constructor() {
        this.ctx = null;
        this.enabled = true;
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) {
                this.ctx = new AudioCtx();
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    playScanTone() {
        if (!this.enabled || !this.ctx) return;
        try {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(440, this.ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(880, this.ctx.currentTime + 0.25);

            gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.25);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start();
            osc.stop(this.ctx.currentTime + 0.25);
        } catch (e) {
            console.warn("Audio error:", e);
        }
    }

    playSuccessTone() {
        if (!this.enabled || !this.ctx) return;
        try {
            const now = this.ctx.currentTime;
            const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
            notes.forEach((freq, index) => {
                const osc = this.ctx.createOscillator();
                const gain = this.ctx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(freq, now + index * 0.07);

                gain.gain.setValueAtTime(0.09, now + index * 0.07);
                gain.gain.exponentialRampToValueAtTime(0.001, now + index * 0.07 + 0.22);

                osc.connect(gain);
                gain.connect(this.ctx.destination);

                osc.start(now + index * 0.07);
                osc.stop(now + index * 0.07 + 0.22);
            });
        } catch (e) {
            console.warn("Audio error:", e);
        }
    }

    playRejectTone() {
        if (!this.enabled || !this.ctx) return;
        try {
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.setValueAtTime(180, now + 0.12);

            gain.gain.setValueAtTime(0.1, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.3);
        } catch (e) {
            console.warn("Audio error:", e);
        }
    }
}

const sounds = new SoundManager();

// The trained model and the simulator use different names for the same material.
function materialKey(className) {
    const key = String(className || '').trim().toLowerCase();
    const aliases = {
        botellas_reciclable: 'botella_plastica_pet', botella_reciclable: 'botella_plastica_pet',
        botella: 'botella_plastica_pet', bottle: 'botella_plastica_pet',
        lata: 'lata_aluminio', latas_reciclable: 'lata_aluminio',
        carton: 'papel_carton', caja_carton: 'papel_carton', papel: 'papel_carton',
        botella_vidrio: 'vidrio', vidrio_reciclable: 'vidrio', glass: 'vidrio',
        tetrapak: 'tetra_pak'
    };
    return aliases[key] || key;
}

// ==========================================================================
// 3. Application State & Controller
// ==========================================================================

const App = {
    currentState: 1, // 1: IDLE, 2: SCANNING, 3: RESULT
    resultDisplayDuration: 4200, // ms
    resultTimeout: null,
    countdownInterval: null,
    isManualSimulation: false,

    // Sistema de Análisis Continuo y Consistencia Temporal Verdadera
    analysisHold: {
        active: false,
        targetClass: null,
        targetConfidence: 0,
        startTime: 0,
        lastSeenTime: 0,
        requiredDuration: 1200, // ms requeridos de presencia continua (1.2 segundos reales)
        graceWindow: 350,       // ms de tolerancia ante jitter o desenfoque puntual
        animFrameId: null,
        simTimeout: null
    },

    elements: {
        // Scanner & Video
        scannerBox: document.getElementById('scanner-box'),
        videoFeed: document.getElementById('main-video-feed'),
        camStandby: document.getElementById('cam-standby'),
        multiWarning: document.getElementById('multi-object-warning'),
        streamStatus: document.getElementById('stream-status-label'),
        scanProgressBar: document.getElementById('scan-progress-bar'),
        scanHudLabel: document.getElementById('scan-hud-label'),

        // Result Modal Elements
        resultModal: document.getElementById('result-modal'),
        resultCard: document.getElementById('result-card-element'),
        resHeaderPill: document.getElementById('res-header-pill'),
        resHeaderIcon: document.getElementById('res-header-icon'),
        resHeaderTitle: document.getElementById('res-header-title'),
        resMaterialBubble: document.getElementById('res-material-bubble'),
        resMaterialIcon: document.getElementById('res-material-icon'),
        resCategoryLabel: document.getElementById('res-category-label'),
        resMaterialName: document.getElementById('res-material-name'),
        resMaterialDesc: document.getElementById('res-material-desc'),
        resConfidenceNum: document.getElementById('res-confidence-num'),

        // Smart Bin Box
        resBinBox: document.getElementById('res-bin-box'),
        resBinIcon: document.getElementById('res-bin-icon'),
        resBinTitle: document.getElementById('res-bin-title'),
        resBinSubtitle: document.getElementById('res-bin-subtitle'),

        // Footer Eco Points & Timer
        resEcopointsText: document.getElementById('res-ecopoints-text'),
        resCountdownNum: document.getElementById('res-countdown-num'),
        resCountdownBar: document.getElementById('res-countdown-bar'),

        // Steps in "Así funciona"
        step1: document.getElementById('step-row-1'),
        step2: document.getElementById('step-row-2'),
        step3: document.getElementById('step-row-3'),

        // Sim Drawer & Buttons
        btnToggleSim: document.getElementById('btn-toggle-sim'),
        simDrawer: document.getElementById('sim-drawer'),
        simCaret: document.getElementById('sim-caret'),
        btnReset: document.getElementById('btn-force-idle'),
        btnAudio: document.getElementById('btn-toggle-audio'),
        iconAudio: document.getElementById('audio-icon')
    },

    init() {
        this.setupEventListeners();
        if (document.body.dataset.interfaceOnly !== 'true') this.connectBackendEvents();
        this.transitionToState(1);
    },

    setupEventListeners() {
        // Init audio on first user click
        document.body.addEventListener('click', () => sounds.init(), { once: true });

        // Toggle Simulation Drawer
        if (this.elements.btnToggleSim && this.elements.simDrawer) {
            this.elements.btnToggleSim.addEventListener('click', () => {
                this.elements.simDrawer.classList.toggle('open');
                if (this.elements.simCaret) {
                    this.elements.simCaret.classList.toggle('ph-caret-down');
                    this.elements.simCaret.classList.toggle('ph-caret-up');
                }
            });
        }

        // Toggle Audio
        if (this.elements.btnAudio) {
            this.elements.btnAudio.addEventListener('click', () => {
                sounds.init();
                sounds.enabled = !sounds.enabled;
                if (sounds.enabled) {
                    this.elements.iconAudio.className = 'ph-bold ph-speaker-high';
                    this.elements.btnAudio.style.color = 'var(--eco-accent)';
                } else {
                    this.elements.iconAudio.className = 'ph-bold ph-speaker-slash';
                    this.elements.btnAudio.style.color = '#94a3b8';
                }
            });
        }

        // Reset Button
        if (this.elements.btnReset) {
            this.elements.btnReset.addEventListener('click', () => {
                this.isManualSimulation = false;
                this.transitionToState(1);
            });
        }

        // Simulation Class Buttons
        document.querySelectorAll('.sim-chip[data-class]').forEach(btn => {
            btn.addEventListener('click', () => {
                const itemClass = btn.getAttribute('data-class');
                const conf = Math.floor(Math.random() * 8) + 92; // 92% - 99%
                this.triggerScanSequence(itemClass, conf / 100, true);
            });
        });
    },

    // ==========================================================================
    // 4. State Machine Transitions & Continuous Temporal Analysis
    // ==========================================================================

    transitionToState(newState, payload = null) {
        this.currentState = newState;
        if (newState !== 3) window.EcoMaterialMedia?.hide();

        // Limpiar temporizadores y loops de animación
        if (this.analysisHold.animFrameId) {
            cancelAnimationFrame(this.analysisHold.animFrameId);
            this.analysisHold.animFrameId = null;
        }
        if (this.analysisHold.simTimeout) {
            clearTimeout(this.analysisHold.simTimeout);
            this.analysisHold.simTimeout = null;
        }
        if (this.resultTimeout) clearTimeout(this.resultTimeout);
        if (this.countdownInterval) clearInterval(this.countdownInterval);

        // Reset active step highlights
        [this.elements.step1, this.elements.step2, this.elements.step3].forEach(st => {
            if (st) st.style.opacity = '1';
        });

        if (newState === 1) {
            // ----------------------------------------------------
            // ESTADO 1: IDLE / INICIO (Pantalla Mockup de Espera)
            // ----------------------------------------------------
            this.analysisHold.active = false;
            this.isManualSimulation = false;

            if (this.elements.scannerBox) this.elements.scannerBox.classList.remove('scanning');
            if (this.elements.resultModal) this.elements.resultModal.classList.remove('active');
            if (this.elements.streamStatus) this.elements.streamStatus.textContent = document.body.dataset.interfaceOnly === 'true' ? 'SIMULACIÓN' : 'EN VIVO';
            if (this.elements.scanProgressBar) this.elements.scanProgressBar.style.width = '0%';
            if (this.elements.scanHudLabel) this.elements.scanHudLabel.textContent = 'ANALIZANDO MATERIAL';
        }
        else if (newState === 2) {
            // ----------------------------------------------------
            // ESTADO 2: SCANNING (Análisis con Verificación en Tiempo Real)
            // ----------------------------------------------------
            if (this.elements.scannerBox) this.elements.scannerBox.classList.add('scanning');
            if (this.elements.resultModal) this.elements.resultModal.classList.remove('active');
            if (this.elements.streamStatus) this.elements.streamStatus.textContent = 'ANALIZANDO';

            const classKey = materialKey(payload ? payload.class_name : 'botella_plastica_pet');
            const itemData = MATERIAL_DATABASE[classKey] || MATERIAL_DATABASE["botella_plastica_pet"];

            // Pre-calentar y almacenar en búfer el video correspondiente durante los 1.2s de análisis
            window.EcoMaterialMedia?.prepare(classKey);

            if (this.elements.scanHudLabel) {
                this.elements.scanHudLabel.textContent = `ANALIZANDO`;
            }

            if (this.elements.step2) {
                this.elements.step2.style.transform = 'translateX(6px)';
                setTimeout(() => { if (this.elements.step2) this.elements.step2.style.transform = 'none'; }, 600);
            }

            sounds.playScanTone();

            // CASO A: SIMULACIÓN MANUAL
            if (this.isManualSimulation) {
                if (this.elements.scanProgressBar) this.elements.scanProgressBar.style.width = '0%';
                const startTime = performance.now();
                const duration = this.analysisHold.requiredDuration;

                const animateSimProgress = (now) => {
                    if (this.currentState !== 2) return;
                    const elapsed = now - startTime;
                    const progress = Math.min(100, (elapsed / duration) * 100);
                    if (this.elements.scanProgressBar) {
                        this.elements.scanProgressBar.style.width = `${progress}%`;
                    }
                    if (elapsed < duration) {
                        this.analysisHold.animFrameId = requestAnimationFrame(animateSimProgress);
                    }
                };
                this.analysisHold.animFrameId = requestAnimationFrame(animateSimProgress);

                this.analysisHold.simTimeout = setTimeout(() => {
                    this.transitionToState(3, payload);
                }, duration);
                return;
            }

            // CASO B: ANÁLISIS REAL CON CÁMARA (Comprobación Continua de Presencia)
            this.analysisHold.active = true;
            this.analysisHold.targetClass = classKey;
            this.analysisHold.targetConfidence = payload ? payload.confidence : 0.90;
            this.analysisHold.startTime = performance.now();
            this.analysisHold.lastSeenTime = performance.now();

            if (this.elements.scanProgressBar) this.elements.scanProgressBar.style.width = '0%';

            const verifyPresenceLoop = (now) => {
                if (this.currentState !== 2 || !this.analysisHold.active) return;

                const timeSinceLastSeen = now - this.analysisHold.lastSeenTime;

                // Si el objeto fue retirado de la cámara por más de la ventana de gracia -> CANCELAR ESCANEO
                if (timeSinceLastSeen > this.analysisHold.graceWindow) {
                    console.log("⚠️ [EcoVision] Objeto retirado de la cámara antes de terminar el análisis. Cancelando escaneo...");
                    this.transitionToState(1);
                    return;
                }

                // Calcular progreso real acumulado
                const elapsedHold = now - this.analysisHold.startTime;
                const progress = Math.min(100, (elapsedHold / this.analysisHold.requiredDuration) * 100);

                if (this.elements.scanProgressBar) {
                    this.elements.scanProgressBar.style.width = `${progress}%`;
                }

                // Si se mantuvo de forma continua y estable por el tiempo requerido -> APROBAR RESULTADO
                if (elapsedHold >= this.analysisHold.requiredDuration) {
                    console.log(`✅ [EcoVision] Detección verificada de forma continua para '${this.analysisHold.targetClass}'. Mostrando resultado.`);
                    this.transitionToState(3, {
                        class_name: this.analysisHold.targetClass,
                        confidence: this.analysisHold.targetConfidence
                    });
                    return;
                }

                this.analysisHold.animFrameId = requestAnimationFrame(verifyPresenceLoop);
            };

            this.analysisHold.animFrameId = requestAnimationFrame(verifyPresenceLoop);
        }
        else if (newState === 3) {
            // ----------------------------------------------------
            // ESTADO 3: RESULTADO (Clasificación & Caneca Asignada)
            // ----------------------------------------------------
            this.analysisHold.active = false;

            if (this.elements.scannerBox) this.elements.scannerBox.classList.remove('scanning');
            if (this.elements.streamStatus) this.elements.streamStatus.textContent = 'RESULTADO';

            const classKey = materialKey(payload ? payload.class_name : 'botella_plastica_pet');
            const itemData = MATERIAL_DATABASE[classKey] || MATERIAL_DATABASE["botella_plastica_pet"];
            const confPct = payload ? Math.round(payload.confidence * 100) : 96;

            this.populateResultCard(itemData, confPct);

            if (this.elements.resultModal) {
                this.elements.resultModal.classList.add('active');
            }

            // Registro automático de latencia (RNF-04): solo en modo real y con detección de la cámara
            if (!this.isManualSimulation && document.body.dataset.interfaceOnly !== 'true' && payload) {
                fetch('/api/latency_mark', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ class_name: payload.class_name, confidence: payload.confidence }),
                    keepalive: true
                }).catch(() => {});
            }
            const hasMedia = Object.hasOwn(MATERIAL_DATABASE, classKey);
            this.elements.resultCard?.classList.toggle('has-material', hasMedia);
            if (hasMedia) window.EcoMaterialMedia?.show(classKey, itemData.name);
            else window.EcoMaterialMedia?.hide();

            if (itemData.isRecyclable) {
                sounds.playSuccessTone();
            } else {
                sounds.playRejectTone();
            }

            // Barra de Cuenta Regresiva para Regreso al Inicio
            let remainingMs = this.resultDisplayDuration;
            const intervalStep = 100;
            if (this.elements.resCountdownNum) this.elements.resCountdownNum.textContent = `${Math.ceil(remainingMs / 1000)}s`;
            if (this.elements.resCountdownBar) this.elements.resCountdownBar.style.width = '100%';

            this.countdownInterval = setInterval(() => {
                remainingMs -= intervalStep;
                const secondsLeft = Math.max(1, Math.ceil(remainingMs / 1000));
                if (this.elements.resCountdownNum) this.elements.resCountdownNum.textContent = `${secondsLeft}s`;

                const progressPct = Math.max(0, (remainingMs / this.resultDisplayDuration) * 100);
                if (this.elements.resCountdownBar) this.elements.resCountdownBar.style.width = `${progressPct}%`;

                if (remainingMs <= 0) {
                    clearInterval(this.countdownInterval);
                }
            }, intervalStep);

            // Retorno Automático al Estado 1 (Mockup de Inicio)
            this.resultTimeout = setTimeout(() => {
                this.transitionToState(1);
            }, this.resultDisplayDuration);
        }
    },

    populateResultCard(itemData, confidence) {
        // Header
        if (itemData.isRecyclable) {
            this.elements.resHeaderPill.className = 'result-modal-header';
            this.elements.resHeaderIcon.className = 'ph-bold ph-check-circle';
            this.elements.resHeaderTitle.textContent = '¡RESIDUO RECICLABLE!';
        } else {
            this.elements.resHeaderPill.className = 'result-modal-header rejected';
            this.elements.resHeaderIcon.className = 'ph-bold ph-x-circle';
            this.elements.resHeaderTitle.textContent = 'RESIDUO NO RECICLABLE';
        }

        // Details
        if (this.elements.resMaterialIcon) this.elements.resMaterialIcon.className = itemData.icon;
        if (this.elements.resCategoryLabel) this.elements.resCategoryLabel.textContent = itemData.category;
        if (this.elements.resMaterialName) this.elements.resMaterialName.textContent = itemData.name;
        if (this.elements.resMaterialDesc) this.elements.resMaterialDesc.textContent = itemData.description;
        if (this.elements.resConfidenceNum) this.elements.resConfidenceNum.textContent = `${confidence}%`;
        if (this.elements.resEcopointsText) {
            this.elements.resEcopointsText.innerHTML = `<i class="ph-fill ph-leaf"></i> <span>${itemData.ecoImpact}</span>`;
        }

        // Bin Destination
        if (this.elements.resBinBox) {
            this.elements.resBinBox.className = `smart-bin-box bin-${itemData.bin}`;
            if (this.elements.resBinTitle) this.elements.resBinTitle.textContent = itemData.binName;
            if (this.elements.resBinSubtitle) this.elements.resBinSubtitle.textContent = itemData.binDescription;

            if (this.elements.resBinIcon) {
                if (itemData.bin === 'blanca') {
                    this.elements.resBinIcon.className = 'ph-fill ph-trash-simple bin-svg-icon';
                } else {
                    this.elements.resBinIcon.className = 'ph-fill ph-trash bin-svg-icon';
                }
            }
        }
    },

    triggerScanSequence(className, confidence = 0.95, isManual = false) {
        if (isManual && document.body.dataset.interfaceOnly !== 'true') return;
        if (!Object.hasOwn(MATERIAL_DATABASE, materialKey(className))) return;
        if (this.currentState === 2 || (this.currentState === 3 && !isManual)) {
            return; // Ya está activo
        }
        this.isManualSimulation = isManual;
        this.transitionToState(2, { class_name: className, confidence });
    },

    // ==========================================================================
    // 5. Backend Event Source (SSE) & Camera Detection Hook
    // ==========================================================================

    connectBackendEvents() {
        if (window.EventSource) {
            try {
                const evtSource = new EventSource('/api/stream');
                this.eventSource = evtSource;
                evtSource.onopen = () => this.stopFallbackPolling();
                evtSource.onmessage = (event) => {
                    this.stopFallbackPolling();
                    try {
                        const data = JSON.parse(event.data);
                        this.handleBackendUpdate(data);
                    } catch (e) {
                        console.error("SSE JSON parse error:", e);
                    }
                };

                evtSource.onerror = () => {
                    this.fallbackPolling();
                };
            } catch (err) {
                this.fallbackPolling();
            }
        } else {
            this.fallbackPolling();
        }
    },

    fallbackPolling() {
        if (this.pollingInterval) return;
        this.pollingInterval = setInterval(async () => {
            if (this.pollingRequest) return;
            const controller = new AbortController();
            this.pollingRequest = controller;
            const timeout = setTimeout(() => controller.abort(), 2000);
            try {
                const response = await fetch('/api/status', { signal: controller.signal });
                if (response.ok) {
                    const data = await response.json();
                    if (this.pollingInterval && this.pollingRequest === controller) this.handleBackendUpdate(data);
                }
            } catch (_) { /* SSE continues its native reconnection in parallel. */ }
            finally {
                clearTimeout(timeout);
                if (this.pollingRequest === controller) this.pollingRequest = null;
            }
        }, 200);
    },

    stopFallbackPolling() {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
        this.pollingRequest?.abort();
        this.pollingRequest = null;
    },

    handleBackendUpdate(data) {
        if (!data) return;

        if (!data.camera_connected && document.body.dataset.interfaceOnly !== 'true') {
            if (this.elements.camStandby) this.elements.camStandby.style.display = 'flex';
            if (this.elements.videoFeed) this.elements.videoFeed.style.display = 'none';
            if (typeof Desktop !== 'undefined') Desktop.alert('La cámara no está disponible. Vuelve al menú para reintentar.');
        }

        // Actualizar estado de la cámara y visibilidad
        if (data.camera_connected) {
            if (this.elements.camStandby) {
                this.elements.camStandby.style.display = 'none';
            }
            if (this.elements.videoFeed) {
                this.elements.videoFeed.style.display = 'block';
            }
            document.querySelector('.session-alert')?.remove();
        }

        // Si la simulación manual está en curso, no sobreescribir con cámara
        if (this.isManualSimulation) return;

        const threshold = data.conf_threshold || 0.75;
        const activeDetection = data.active_detection;

        // 0. Varios objetos sobre el umbral a la vez -> avisar y no clasificar ninguno (RF-09)
        const multipleObjects = Boolean(data.multiple_objects) || (data.detection_count || 0) > 1;
        if (this.elements.multiWarning) {
            this.elements.multiWarning.style.display = (multipleObjects && this.currentState !== 3) ? 'flex' : 'none';
        }
        if (multipleObjects) {
            if (this.currentState === 2) {
                console.warn("⚠️ [EcoVision] Más de un objeto en el encuadre. Análisis cancelado hasta que quede uno solo.");
                this.transitionToState(1);
            }
            return;
        }

        // 1. Si estamos en ESTADO 1 (IDLE) y llega una detección válida -> Iniciar análisis
        if (this.currentState === 1) {
            if (activeDetection && activeDetection.class_name && activeDetection.confidence >= threshold) {
                this.triggerScanSequence(activeDetection.class_name, activeDetection.confidence, false);
            }
        }

        // 2. Si estamos en ESTADO 2 (SCANNING) -> Validar presencia continua
        else if (this.currentState === 2 && this.analysisHold.active) {
            if (activeDetection && activeDetection.class_name && activeDetection.confidence >= (threshold - 0.12)) {
                // Si la clase coincide o es compatible, refrescar el timestamp de presencia
                this.analysisHold.lastSeenTime = performance.now();
                this.analysisHold.targetConfidence = Math.max(this.analysisHold.targetConfidence, activeDetection.confidence);

                // Si la clase detectada cambia de forma persistente a otra clase válida, actualizarla
                if (materialKey(activeDetection.class_name) !== this.analysisHold.targetClass && activeDetection.confidence >= threshold) {
                    this.analysisHold.targetClass = materialKey(activeDetection.class_name);
                    const itemData = MATERIAL_DATABASE[this.analysisHold.targetClass] || MATERIAL_DATABASE["botella_plastica_pet"];
                    if (this.elements.scanHudLabel) {
                        this.elements.scanHudLabel.textContent = `ANALIZANDO`;
                    }
                }
            }
        }
    }
};

// Global video error handler con auto-reconexión continua
function handleVideoError(img) {
    if (document.body.dataset.interfaceOnly === 'true' || !img.hasAttribute('src')) return;
    console.warn("⚠️ [EcoVision] Reintentando conexión con stream de video...");
    const standby = document.getElementById('cam-standby');
    if (standby) standby.style.display = 'flex';

    setTimeout(() => {
        if (img && document.body.dataset.interfaceOnly !== 'true' && img.hasAttribute('src')) {
            img.src = '/video_feed?t=' + Date.now();
            img.style.display = 'block';
        }
    }, 1000);
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

window.addEventListener('pagehide', () => {
    App.stopFallbackPolling();
    App.eventSource?.close();
});
window.addEventListener('pageshow', event => {
    if (event.persisted && document.body.dataset.interfaceOnly !== 'true') App.connectBackendEvents();
});
