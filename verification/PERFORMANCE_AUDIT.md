# Auditoría de rendimiento — EcoVision

## Estado actual: reproducción de videos locales

Se retiró la generación gráfica durante la ejecución. La interfaz usa un único
reproductor HTML y un mapa de videos. PET es el único material con video recibido;
los otros seis conservan su SVG. Se retiraron el motor Three.js, las mallas,
precargas, la ruta auxiliar de módulos y las pruebas/capturas de los modelos anteriores.

### Archivo integrado

- Fuente: `C:/Users/Santi/Downloads/el_la_etiqueta_pon_el_logo_de.mp4` (original conservado).
- Destino: `static/videos/botella_plastica_pet.mp4` (copia idéntica, 1.279.735 bytes).
- Resolución 720×1280, 24 FPS, 240 frames, duración 10 s, video H.264.
- Póster JPEG 288×512 extraído del primer frame, sin generación de imagen.
- Sin recodificación, recorte ni aceleración; reproducción siempre silenciada.
- Resultado de 4,2 s: muestra una parte del clip. Una vuelta completa requeriría
  preparar una versión más corta o cambiar el tiempo de resultado deliberadamente.

### Optimizaciones y límites

- No hay geometrías, shaders, contextos gráficos ni animación JS para los objetos.
- Un solo elemento de video. Sin fuente MP4 en reposo/escaneo ni para materiales
  pendientes; se descarga únicamente el clip seleccionado.
- Se pausa al perder foco u ocultarse la página; se retira la fuente al cerrar el
  resultado, cambiar de categoría o salir de página. El navegador gestiona su caché.
- Movimiento reducido usa solo el póster; sin MP4 ni decodificación de video.
- Carga lenta, autoplay bloqueado o error no bloquean la cuenta regresiva.
- Se conserva la corrección previa de SSE/polling: un intervalo y una solicitud
  en curso, cancelados al recuperar SSE; timeout de petición de 2 s.
- Se retiraron 720.032 bytes de bibliotecas Three.js, además de scripts propios,
  licencia y evidencia visual obsoleta. El nuevo MP4 añade 1,28 MB al disco: no se
  afirma que el cambio reduzca el peso total del proyecto.
- La decodificación también consume recursos. No se midió todavía ahorro de CPU
  ni FPS con YOLO/cámara activos; la aceleración depende del equipo y del códec.
- Siguiente mejora del archivo: comparar un derivado 288×512 o 360×640 H.264 sin
  audio frente al original, conservando la etiqueta y la nitidez a tamaño real.

### Comprobaciones de esta integración

15 grupos de pruebas aprobados en Edge, sin errores de JavaScript. El MP4 se
decodificó y avanzó; la duración reportada por el navegador fue 10,005 s. Se verificó
que la copia y el original tienen el mismo SHA-256 y que Flask sirve solicitudes
de rango con HTTP 206 y `Content-Type: video/mp4`. Capturas y detalle en `results.json`.
La máscara CSS suaviza únicamente los márgenes vacíos del clip sobre la tarjeta;
no modifica el archivo ni genera imágenes por frame.

## Oportunidades pendientes, por prioridad

| Prioridad | Evidencia actual | Cambio propuesto y criterio de aceptación |
|---|---|---|
| P1, antes de limitar YOLO | `realtime_ui_app.py`, `get_status`: `active_detection` no caduca; solo se ocultan las cajas antiguas después de 0,5 s. | Publicar la edad/fecha de la detección y rechazar datos vencidos en frontend. Probar que retirar un objeto o detener la inferencia cancela el análisis. |
| P2 | `_inference_loop` copia el último frame y ejecuta YOLO continuamente, sin secuencia de frame. | Consumir solo frames nuevos mediante secuencia/Condition; medir tasa y latencia. Un filtro de movimiento requiere detecciones frescas periódicas para conservar la verificación de presencia. |
| P2 | `_capture_and_stream_loop` copia y dibuja sobre 1280×720; copia otra vez para HUD; solo después reduce a 640×360. | Reducir primero la copia de visualización, escalar cajas y mezclar únicamente la región del HUD. El destino tiene cuatro veces menos píxeles. Conservar el frame original para inferencia. |
| P2 | Se codifica JPEG continuamente; `generate_video_stream` transmite cada 30 ms incluso el mismo JPEG. | Publicar con número de secuencia y codificar solo si hay consumidores. Verificar reconexión inmediata y mantener inferencia si se necesita clasificación. |
| P2 | `templates/index.html` conserva Google Fonts y script de iconos externo. En capturas sin red pueden faltar iconos. | Empaquetar localmente las fuentes/pesos e iconos usados. Comprobar arranque con red deshabilitada. Los videos ya son locales. |
| P3 | Imágenes PNG activas: ~3,05 MiB comprimidos; ~28,89 MiB RGBA teóricos contando favicon. Cámara 1024² mostrada a 96×96; planeta/caneca 1254²; logo 2090×615. | Crear derivados al tamaño visible × DPR máximo y formatos con alfa optimizados; conservar originales. Medir transferencia y memoria decodificada, no deducir memoria real de estos cálculos. |
| P3 | `static/css/style.css`: animaciones decorativas perpetuas, blur del backdrop y láser que anima `top`. | Pausar decoración detrás del modal, ampliar movimiento reducido a CSS general y animar con transform. Comparar GPU/fluidez antes de ajustar blur. |
| P3, clasificación | Etiquetas YOLO desconocidas aún usan los textos PET heredados, aunque no activan una vista de material. | Confirmar `model.names` reales y definir una tarjeta neutral sin afirmar reciclabilidad. No inventar equivalencias entre clases ambiguas. |

## Validación reproducible

1. Ejecutar Flask sin iniciar cámara:
   `python -X utf8 -c "from realtime_ui_app import app; app.run(host='127.0.0.1', port=5055, debug=False, threaded=True, use_reloader=False)"`.
2. Con Playwright en `NODE_PATH`, ejecutar `node verification/check-ui.cjs`.
3. Revisar `results.json`, `video-pet-desktop.png` y `video-pet-390.png`.
   Se verifica decodificación y avance del MP4 real, pausa/liberación, alias,
   materiales pendientes, fallos, movimiento reducido, carga lenta y retorno.
   Los eventos de foco/visibilidad son simulados; no prueban minimizar PyWebView.
4. `video-preview.html` es una tarjeta de revisión con reproducción continua;
   no ejecuta detección ni modifica la duración de resultado de la aplicación.
5. Validación física pendiente: `python realtime_ui_app.py --cam 1`. Medir 60 s
   por estado con igual cámara, iluminación, peso y equipo: CPU/RSS de Python y
   WebView, CAM FPS, AI FPS y latencia. Probar retirada del residuo y reconexión.

El frontend admite vidrio, pero el modelo entrenado debe incluir esa clase para
su detección real. No se cambiaron pesos, umbrales ni el pipeline de inferencia.
