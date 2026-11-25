# ♻️ Sistema de Visión Artificial para Identificación de Materiales Reciclables

> **EcoVision Desktop 0.2.0:** abre `EcoVision Desarrollo.vbs` para trabajar con el proyecto local, o `dist/EcoVision/EcoVision.exe` para usar la distribución. El menú permite elegir Simulación o Prueba real. Guía de instalación offline, recarga, versiones y modelo provisional: [DESKTOP.md](DESKTOP.md).

Proyecto de opción de grado — Ingeniería de Sistemas, Politécnico Grancolombiano.

Aplicación de escritorio que usa visión artificial (YOLO) para clasificar residuos como reciclables o no reciclables en tiempo real, desplegada en un televisor institucional mediante conexión HDMI.

---

## 📋 Descripción del Proyecto

En los puntos ecológicos institucionales, la contaminación cruzada de residuos ocurre principalmente por falta de orientación inmediata al usuario. Este sistema detecta el residuo mostrado frente a una cámara y responde con una clasificación binaria/especializada:

- **Reciclable** → indica el tipo de material (ej. "Botella PET") y el porcentaje de confianza.
- **No reciclable** → mensaje directo, orientando el desecho a la caneca de no aprovechables.

---

## 🏗️ Arquitectura

Aplicación de escritorio nativa (**Python + PyWebView**) conectada por HDMI al televisor. Incluye un servidor Flask interno en `127.0.0.1`; no necesita un servidor externo ni internet para operar.

### Máquina de 3 Estados (Frontend)

```
[ESTADO 1: INICIO] ──► [ESTADO 2: CARGA] ──► [ESTADO 3: RESULTADO]
"Acerca tu residuo"     "Analizando..."       "Botella PET: Reciclable"
(animación de espera)   (1.0s - 1.5s)          o "No es reciclable"
                                                (retorna a Estado 1 tras 4-5s)
```

### Pipeline de Backend

```
1. Captura USB (OpenCV, solicita 1280×720 @ 30 FPS)
        ↓
2. Hilo de captura y transmisión MJPEG (640×360)
        ↓
3. Hilo independiente de inferencia YOLO (imgsz=320)
```

Actualmente la inferencia es continua; el filtro de movimiento es una mejora
pendiente. La tasa real de captura/inferencia depende del equipo y debe medirse.
La interfaz reproduce videos locales en un único elemento de video. PET tiene
el clip suministrado; los otros seis materiales conservan ilustraciones estáticas. Consulta
`README_INTERFAZ.md` y `verification/PERFORMANCE_AUDIT.md` para límites y validación.

---

## 🧩 Módulos

### Módulo 1 — Frontend (HTML5 / CSS3 / JS)
- Ventana de escritorio a pantalla completa vía PyWebView.
- Puente JS API ↔ Python para comunicar estados.
- Picture-in-picture opcional (240×180px) para mostrar el video en vivo, activable/desactivable en código.

### Módulo 2 — Backend de Detección (Python + OpenCV + YOLO)
- Captura de cámara web USB Full HD.
- Frame differencing para detección de movimiento.
- Modelo **YOLO Nano** (yolov8n / yolov11n) exportado a ONNX.

**Clases del peso provisional actual (`model/best.pt`):**
| # | Clase | Descripción |
|---|-------|-------------|
| 1 | `botella_reciclable` | Botella; se representa como PET en la interfaz |
| 2 | `carton` | Cartón; se representa como Papel / Cartón en la interfaz |

El entrenamiento está incompleto. Lata, Tetra Pak, vidrio y no aprovechable pueden explorarse en la simulación; su presencia en la interfaz no prueba que el modelo los reconozca.

---

## 📊 Dataset y Entrenamiento

```
Recolección de Campo ──► Etiquetado Roboflow ──► Data Augmentation ──► Entrenamiento Colab
250 fotos/clase          Bounding Boxes          Rotaciones ±15°       YOLO Nano
Variación de luz          Exportación YOLO        Brillo ±20%           GPU T4 (Cloud)
Enteros/aplastados                                Desenfoque movimiento  Genera best.pt
```

- **Volumen objetivo:** 200–300 fotos por clase, tomadas en cafeterías, pasillos y puntos ecológicos del campus, en distintas condiciones de luz.
- **Variabilidad:** objetos aplastados, sin tapa, con etiqueta rota, en distintos ángulos.
- **Anotación:** Roboflow (bounding boxes + augmentation).
- **Registro de métricas:** cada detección exitosa se guarda en `estadisticas_reciclaje.csv` (fecha, hora, clase, % de confianza) para el informe final.

---

## 🛠️ Stack Tecnológico

- **Backend:** Python, OpenCV, YOLO (Ultralytics), ONNX Runtime
- **Frontend:** HTML5, CSS3, JavaScript
- **Empaquetado desktop:** PyWebView
- **Entrenamiento:** Google Colab (GPU T4)
- **Etiquetado:** Roboflow
- **Hardware:** Cámara web USB 1080p, TV institucional (HDMI)

---

## 📁 Estructura de Carpetas Sugerida

```
proyecto-reciclaje/
├── backend/
│   ├── main.py                  # Entry point (PyWebView + loop de captura)
│   ├── camera.py                 # Captura OpenCV + frame differencing
│   ├── inference.py               # Carga y ejecución del modelo ONNX
│   └── logger.py                  # Registro en estadisticas_reciclaje.csv
├── frontend/
│   ├── index.html                 # Máquina de 3 estados
│   ├── style.css
│   └── app.js                     # Puente JS API
├── model/
│   └── best.onnx                  # Modelo exportado
├── dataset/                       # (no versionar imágenes pesadas, usar .gitignore)
├── estadisticas_reciclaje.csv
├── requirements.txt
└── README.md
```

---

## 💰 Presupuesto Consolidado

| Componente | Especificación | Costo Estimado (COP) |
|---|---|---|
| Unidad de Cómputo | Portátil de desarrollo (sin suspensión) | $0 |
| Sensor de Visión | Cámara Web USB Full HD 1080p (UVC) | ~$55.000 |
| Dispositivo de Salida | TV institucional (HDMI) | $0 |
| Cableado | Cable HDMI + extensión USB activa 2m | ~$25.000 |
| **Total** | | **~$80.000 COP** |

---

## 🗓️ Roadmap de Ejecución

- [ ] **Semana 1:** Montaje base en VS Code (PyWebView + OpenCV + interfaz de 3 pantallas).
- [ ] **Semana 2:** Sesión de recolección de fotos en campus + etiquetado en Roboflow.
- [ ] **Semana 3:** Entrenamiento YOLO Nano en Colab (GPU T4) + exportación a ONNX.
- [ ] **Semana 4:** Pruebas integradas en el punto ecológico + redacción del informe de métricas.

---

## 🚀 Puesta en Marcha

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la Aplicación de Escritorio (Ventana Nativa PyWebView)
python realtime_ui_app.py

# 3. Modo Kiosco / Pantalla Completa (Ideal para TV institucional por HDMI)
python realtime_ui_app.py --fullscreen

# Elegir cámara o probar únicamente la interfaz de escritorio
python realtime_ui_app.py --cam1       # índice OpenCV 0
python realtime_ui_app.py --cam2       # índice OpenCV 1
python realtime_ui_app.py --sin-camara # simulador, sin cámara ni modelo

# 4. Modo alternativo (solo ventana OpenCV tradicional)
python realtime_cam.py
```

`requirements.txt`:
```
ultralytics>=8.0.0
opencv-python>=4.8.0
numpy>=1.24.0
onnxruntime>=1.16.0
pywebview>=4.0.0
Flask>=3.0.0
```

---

## 📄 Licencia

Proyecto académico — Politécnico Grancolombiano.
