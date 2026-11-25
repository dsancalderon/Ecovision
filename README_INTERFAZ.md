# ♻️ EcoVision — Guía de Uso de la Aplicación de Escritorio

> **Nuevo flujo Desktop 0.2.0:** consulta [DESKTOP.md](DESKTOP.md). El arranque normal muestra carga y menú; Simulación oculta el visor y no abre cámara ni modelo, mientras Prueba real activa el motor y oculta los controles de simulación. `EcoVision Desarrollo.vbs` recarga los cambios locales sin volver a empaquetar. La distribución está en `dist/EcoVision`.

Esta aplicación de escritorio nativa (**Python + PyWebView**) implementa la máquina de 3 estados requerida para el punto ecológico institucional, combinando visión artificial en tiempo real con una interfaz gráfica moderna (HTML5/CSS3/JS) y una cámara en miniatura (*Picture-in-Picture*) en la esquina superior derecha, **desplegada directamente en una ventana nativa de escritorio (sin requerir abrir navegadores externos)**.

---

## 🚀 Cómo Ejecutar la Aplicación de Escritorio

Abre tu terminal en la carpeta del proyecto y ejecuta:

```bash
python realtime_ui_app.py
```

Automáticamente:
1. Cargará tu modelo (`best.pt` o `yolov8n.pt`).
2. Activará la cámara web con inferencia YOLO en tiempo real.
3. **Abrirá directamente la Ventana de Escritorio Nativa (PyWebView) en tu pantalla.**

### Videos de materiales

El resultado de botella PET reproduce el video local suministrado por el usuario:
`static/videos/botella_plastica_pet.mp4`. Se reconoce con `botella_plastica_pet`,
`Botellas_reciclable`, `botella_reciclable`, `botella` y `bottle`, sin distinguir
mayúsculas. El archivo conserva sus 10 segundos, 720×1280 y 24 FPS; se reproduce
silenciado y a velocidad original. El resultado mantiene su duración de 4,2 s,
por lo que muestra el inicio del clip y luego vuelve a espera.

El reproductor usa un solo elemento `<video>` y `static/js/material-media.js`.
Solo adjunta el MP4 al entrar al resultado correspondiente. Al regresar a espera,
iniciar escaneo, cambiar a un material sin video o salir de página, pausa y retira
la fuente. Al ocultar la ventana o perder foco pausa; al volver continúa.
Con movimiento reducido muestra únicamente el póster extraído del propio video.
La carga y reproducción nunca bloquean la clasificación ni su cuenta regresiva.

Lata, cartón, Tetra Pak, vidrio y no aprovechable tienen ilustraciones SVG
estáticas hasta recibir sus videos. No se generan objetos durante la ejecución.
La lógica de geometría, el motor Three.js y el antiguo visor se retiraron.
Videos, fuentes e iconos se sirven desde archivos locales. PET y cartón cuentan
con video; los materiales sin un archivo presente conservan sus ilustraciones SVG.

Para probarlo, abre «Simulador de Residuos» y selecciona «Botella PET».
`verification/video-preview.html` muestra la tarjeta con reproducción continua
para revisar el aspecto sin cámara ni cuenta regresiva real.
Los recursos `*_clean.png` del planeta y la caneca siguen en uso.
Agregar videos no entrena YOLO ni añade clases al peso cargado.

### Parámetros de ejecución

- **Modo Kiosco / Pantalla Completa (Ideal para TV institucional por HDMI):**
  ```bash
  python realtime_ui_app.py --fullscreen
  ```
- **Ajustar el umbral de confianza YOLO:**
  ```bash
  python realtime_ui_app.py --conf 0.50
  ```
- **Primera cámara (índice OpenCV 0):**
  ```bash
  python realtime_ui_app.py --cam1
  ```
- **Segunda cámara (índice OpenCV 1):**
  ```bash
  python realtime_ui_app.py --cam2
  ```
- **Solo interfaz y simulaciones (sin cámara ni carga del modelo):**
  ```bash
  python realtime_ui_app.py --sin-camara
  ```
- **Otro índice de cámara:**
  ```bash
  python realtime_ui_app.py --cam 2
  ```
  Los índices dependen de Windows/OpenCV. Si el índice elegido no existe, la app
  muestra el estado de cámara en espera; no cambia de cámara silenciosamente.
- **Modo navegador web (opcional si deseas abrirlo en navegador):**
  ```bash
  python realtime_ui_app.py --browser
  ```

---

## 🔄 Máquina de 3 Estados

```
[ESTADO 1: ESPERA] ──────► [ESTADO 2: ESCANEANDO] ──────► [ESTADO 3: RESULTADO]
"Acerca tu residuo"        "Analizando material..."       "Botella PET: Reciclable"
(Animación de radar)       (Láser de escaneo ~1.3s)       (Caneca asignada ~4.5s)
                                                                 │
                                                                 ▼
                                                        Retorna a Estado 1
```

1. **Estado 1 (Inicio / Espera):**
   - Animación guía invitando al usuario a acercar el objeto.
   - Ondas concéntricas tipo radar y recordatorio de residuos comunes.
2. **Estado 2 (Carga / Escaneo):**
   - Se activa cuando la cámara detecta un objeto o al presionar un botón de prueba.
   - Barrido con haz láser verde/cian y medidor de confianza en tiempo real.
   - Efecto sonoro futurista de escaneo.
3. **Estado 3 (Resultado / Clasificación):**
   - Muestra el material detectado, porcentaje de confianza e impacto ecológico (EcoPuntos y CO₂ ahorrado).
   - **Iluminación LED de la Caneca Correspondiente:**
     - **Caneca Blanca:** Plásticos aprovechables (PET), Latas de aluminio, Tetra Pak, Papel y Cartón limpio.
     - **Caneca Negra:** Residuos no aprovechables / servilletas sucias.
   - Cuenta regresiva con barra de progreso circular para retornar automáticamente al Estado 1.

---

## 📷 Cámara Picture-in-Picture (PiP) — Arriba a la Derecha

- **Feed en vivo:** Muestra la transmisión de la cámara con las bounding boxes estilizadas y etiquetas de clase.
- **HUD informativo:** Muestra los FPS en tiempo real y el estado del sistema (`STANDBY`, `SCANNING...`, `RESULT READY`).
- **Controles:** Botón para minimizar o expandir el visor de la cámara en cualquier momento.

---

## 🧪 Panel de Pruebas y Simulación (Barra Inferior)

En la parte inferior de la pantalla encontrarás botones de prueba rápida para simular cada clase de residuo sin necesidad de tener el objeto físico frente a la cámara:
- 🍾 **Botella PET**
- 🥫 **Lata Aluminio**
- 🧃 **Tetra Pak**
- 📦 **Papel / Cartón**
- 🍾 **Vidrio**
- ❌ **No Reciclable**
- 🔄 **Reiniciar a Estado 1**
- 🔊 **Activar / Silenciar Sonido**

---

## Guía para integrar nuevos videos

1. Guardar el MP4 en `static/videos/<clase>.mp4` y su póster en la misma carpeta.
2. Registrar `src` y `poster` en el mapa `MEDIA` de `static/js/material-media.js`.
   Registrar únicamente archivos que ya existen; no crear URLs vacías para clases pendientes.
3. Mantener un solo reproductor, sin controles ni audio, y `object-fit: contain`
   para conservar el objeto completo. No cargar todos los videos al iniciar.
4. Conservar el SVG de cada material como último respaldo. El póster cubre carga
   lenta, bloqueo de autoplay o archivo incompatible; el SVG también cubre fallo del póster.
5. La vista no controla la cuenta regresiva ni cambia la máquina de estados.
6. Revisar encuadre, compatibilidad y bucle con el archivo real. No asumir que
   un video generado tiene una vuelta exacta o una unión perfecta.
7. Preferir H.264/MP4 compatible con el WebView del equipo; reducir resolución y
   quitar la pista de audio al preparar versiones optimizadas si procede. El clip
   PET actual se conserva sin recodificar para evaluar el resultado original.

Ver `verification/PERFORMANCE_AUDIT.md` para prioridades y mediciones pendientes.
Ejecutar `verification/check-desktop.cjs` con Playwright/Edge y el backend de
desarrollo en el puerto 5070; `check-ui.cjs` corresponde al flujo anterior.
Las pruebas de interfaz no sustituyen las pruebas físicas de cámara e inferencia.
