# Auditoría de código de EcoVision

Fecha: 13 de octubre de 2026 (America/Bogota).
Estado: revisión y propuestas; cambios de implementación pendientes de aprobación.
Skill aplicada: `code-reviewer`.

## Alcance y conclusión

Revisión del servidor Flask, captura e inferencia, interfaz y medios, herramientas
de cámara/dataset, procesamiento de videos, dependencias y pruebas existentes.
No se modificaron archivos de implementación, modelos, medios ni umbrales.

La separación de captura e inferencia es una buena base. La prioridad es corregir
la frescura y consistencia de detecciones antes de optimizar carga de CPU: hoy el
frontend puede aceptar resultados antiguos o mezclar tiempo/confianza entre clases.
Las propuestas de ahorro eliminan trabajo duplicado manteniendo resolución de
inferencia, pesos y comportamiento de los materiales conocidos.

## Evidencia reproducida en esta revisión

1. **Detección vencida:** se construyó el gestor sin cargar modelo ni abrir cámara,
   con `last_infer_time` de hace 60 segundos y cámara desconectada. `get_status()`
   devolvió todavía la botella con confianza 0.99 como `active_detection`.
2. **Inferencia duplicada:** con un modelo de prueba que devuelve cero cajas y un
   único `raw_frame`, `_inference_loop` llamó a `predict` 14 veces en aproximadamente
   150 ms. Esto demuestra duplicación; no mide la velocidad ni CPU del YOLO real.
3. **Presencia antigua aceptada:** ejecutando el JS real en Node VM con DOM y reloj
   simulados, repetir la misma detección sin cámara llevó al estado de resultado.
4. **Cambio de clase sin estabilidad:** tras 1.2 s de botella al 99 %, cambiar a
   cartón al 70 % completó el resultado de cartón inmediatamente, mostrando 99 %.
   El acumulador no reinició tiempo ni confianza al cambiar de clase.
5. **Clase desconocida:** `unknown_material` al 98 % mostró “Botella Plástica PET”,
   “¡RESIDUO RECICLABLE!” y “CANECA BLANCA”.
6. **Validación de API:** con el cliente de pruebas Flask, `confidence: "abc"` y
   un JSON que es lista devolvieron 500; `confidence: 2` devolvió 200.
7. **Modelo real:** se cargó `model/best.pt` y se leyó `model.names`:
   `{0: 'botella_reciclable', 1: 'carton'}`. No se ejecutó inferencia física.
8. **Sintaxis:** los cuatro scripts Python se analizaron con AST sin errores;
   `node --check` pasó para `app.js` y `material-media.js`.

Se intentó validación en Edge headless, pero el navegador no arrancó correctamente
en el entorno restringido. No hay validación visual actual ni mediciones de
CPU/RSS/FPS con cámara. Las pruebas de Node VM comprueban lógica, no reproducción
real, diseño ni comportamiento de PyWebView.

## Propuestas para aprobar

### A. Detecciones frescas y clasificación consistente — prioridad alta

Evidencia: `realtime_ui_app.py:223-280,289-319,362-370`;
`static/js/app.js:423-465,476-488,627-669`.

- Publicar secuencia y tiempo monotónico del fotograma capturado y de la inferencia.
- Invalidar detecciones cuando falla captura, se interrumpe inferencia o vencen.
  Un frame reutilizado para mostrar video no debe contar como captura nueva.
- Impedir que SSE repetido renueve la presencia de una observación vieja.
- Reiniciar tiempo y confianza al cambiar de clase; conservar aliases equivalentes.
- Mostrar una tarjeta neutral para clases desconocidas, sin asignar una caneca.
- Registrar errores de inferencia con frecuencia limitada en lugar de `except: pass`.

Aceptación: retirar el objeto, congelar captura o interrumpir YOLO cancela el análisis;
un material diferente requiere su propio periodo estable y su propia confianza.
La caducidad se calibra con latencia real para evitar rechazos por hardware lento.
Se mantienen el escaneo de 1.2 s y resultado de 4.2 s para detecciones válidas.

### B. Inferir únicamente el fotograma nuevo más reciente — prioridad alta

Evidencia: `realtime_ui_app.py:227-244,282-283`.

Usar contador de secuencia y `threading.Condition` para despertar inferencia cuando
hay una captura nueva. Si llegan varias durante una inferencia, consumir la última
sin formar una cola creciente. Mantener original para YOLO e `imgsz=320`.

Aceptación: una secuencia no se infiere dos veces; sin capturas nuevas el hilo espera;
se mantiene detección de objetos inmóviles y no aumenta latencia frente a la base.
Implementar después de A. No sustituir por un filtro que infiera solo con movimiento.

### C. Optimizar la preparación de la vista de cámara — prioridad media

Evidencia: `realtime_ui_app.py:325-349`.

Redimensionar la copia de visualización a 640×360 antes de dibujar y mezclar el HUD;
escalar coordenadas y limitar `addWeighted` a la franja del HUD. Mantener intacto el
frame original de inferencia. Actualmente se copia y mezcla toda la imagen grande.

La vista tiene cuatro veces menos píxeles que 1280×720. Esto no equivale a prometer
cuatro veces más FPS: hay que medir. Ajustar tipografía/grosor para conservar legibilidad.

Aceptación: cajas correctamente alineadas y HUD legible; comparar tiempo de render,
CPU y FPS con el mismo origen y número de cajas.

### D. MJPEG sin duplicados y trabajo según consumidores — prioridad media

Evidencia: `realtime_ui_app.py:347-356,410-418`.

Publicar JPEG con secuencia y despertar cada consumidor solo al cambiar. Codificar
una vez para todos; omitir render/JPEG cuando no hay consumidores, conservando captura
e inferencia. Servir placeholder inicial y cerrar generadores limpiamente.

Aceptación: primer frame y reconexión rápidos; un cliente lento no bloquea cámara;
varios clientes no multiplican codificación; desconectarlos no apaga clasificación.

### E. Medios disponibles y ciclo de vida eficiente — prioridad media

Evidencia: `templates/index.html:306`; `static/js/material-media.js:13-41,51-62,97-118,165-209`.

Solo existen MP4/póster de PET y cartón, pero MEDIA declara siete. Se intentan rutas
inexistentes de los otros cinco. El HTML precarga PET; `releaseVideo()` ya no retira
`src`. No hay gestión de `blur/focus` ni consulta JS de movimiento reducido.
El segundo rechazo del reintento de autoplay tampoco verifica `generation`.

- Declarar disponibilidad real y usar directamente SVG para clips ausentes.
- Mantener precarga selectiva durante el escaneo para que el resultado abra rápido.
- Liberar fuentes al ocultar o cambiar material y respetar movimiento reducido.
- Proteger todas las resoluciones/rechazos asíncronos contra cambios de generación.
- Pausar en pérdida de foco y reanudar solo si el resultado sigue activo.

Aceptación: PET y cartón se reproducen en la aplicación real; sin 404 de materiales
pendientes; cambio rápido/error/reintento antiguo no afecta al clip actual; medir
arranque en frío para no introducir una demora perceptible.

### F. Recursos locales y derivados de imágenes — prioridad media/baja

Evidencia: `templates/index.html:10-18`; `static/images`; `static/css/style.css:191,204,330,992-993`.

- Empaquetar fuentes e iconos usados para funcionamiento sin internet.
- Crear derivados de imágenes adecuados a tamaño visible y DPR, preservando originales
  y alfa. Solo los PNG activos se evalúan, no eliminar recursos por nombre duplicado.
- Pausar decoración que queda detrás del resultado y cambiar láser de `top` a
  `transform`; ampliar movimiento reducido al CSS general.
- Evaluar por separado blur y derivados de video, con comparación visual en TV.

Aceptación: apariencia/legibilidad equivalentes, sin símbolos faltantes offline;
medir transferencia y fluidez. La recodificación de videos requiere aprobación
específica: conservar originales, duración, velocidad, encuadre y etiqueta.

### G. Arranque, cámara y cierre robustos — prioridad media

Evidencia: `realtime_ui_app.py:41-53,182-221,289-319,373-377,506-508`;
`realtime_cam.py:29-41,98,150`.

- Resolver modelos/iconos respecto al directorio del script, no al directorio de ejecución.
- Publicar salud real de captura; `isOpened()` no demuestra que `read()` entregue frames.
- Reconectar cámara con espera progresiva y borrar detecciones al desconectarse.
- Liberar la captura anterior antes de reemplazarla en fallback.
- Señalizar salida, despertar esperas y finalizar hilos antes de liberar recursos.
- Comprobar disponibilidad del servidor en vez de esperar siempre 0.8 s.
- Corregir `realtime_cam.py`: `--conf` se lee pero luego se reemplaza por 0.65.

Aceptación: lanzar desde otra carpeta usa el modelo entrenado; reconexión sin estado
antiguo; cierre limpio; `--conf` conserva el valor solicitado.

### H. Validación, pruebas y reproducibilidad — prioridad media

Evidencia: `realtime_ui_app.py:451-461`; `requirements.txt`;
`verification/check-ui.cjs`; `verification/results.json`; `scripts/process_material_video.py`.

- Validar que JSON sea objeto y que confianza sea finita dentro de [0,1], devolviendo 400.
- Actualizar pruebas: aún esperan seis materiales sin video, ausencia de precarga,
  liberación de `src`, pausa por blur y movimiento reducido que ya no reflejan el código.
- El test de cartón edita una vista previa; agregar prueba sobre la aplicación real
  que confirme carga, avance y transición de la categoría.
- Fijar versiones compatibles después de validar el entorno real, sin actualizar todas
  las dependencias simultáneamente. Los mínimos actuales permiten cambios amplios.
- Procesar videos a temporales y reemplazarlos al verificar video y póster; seleccionar
  el stream de video explícitamente y manejar fallos de póster sin un falso “listo”.
- Añadir pruebas de los errores reproducidos y registro de latencia/CPU/RSS antes/después.

Aceptación: API rechaza datos inválidos; fallo de procesamiento conserva entregable
anterior; reportes nuevos identifican entorno y no reutilizan aprobaciones antiguas.

## Límites funcionales actuales

El modelo cargado solo reconoce botella y cartón. La interfaz/simulador tiene otros
materiales, pero optimizar el código no añade clases al modelo. Añadir detección real
requiere dataset, entrenamiento y validación propios; queda fuera de estos paquetes.

No se recomienda cambiar pesos, cuantizar, reducir `imgsz`, subir confianza, recortar
el encuadre ni bajar la tasa de inferencia arbitrariamente como primera optimización.
Esas decisiones pueden afectar detección o latencia y requieren evaluación separada.

## Orden sugerido y criterio de finalización

Primera fase: A + B + C + E + H (validación API y pruebas de regresión).
Segunda fase: D + G. Tercera fase opcional: F y reproducibilidad/medios restantes de H.

Antes de implementación: copia recuperable de código; esta carpeta no tiene `.git`.
Antes/después: medir con el mismo modelo, cámara, escena, iluminación y equipo.
Comparar CPU/RSS, FPS de captura e inferencia, latencia y aparición del video; verificar
retiro de objeto, cambio de material, desconexión/reconexión y cierre de PyWebView.
Aceptar cada paquete solo si mejora su métrica sin una regresión funcional/visual.
No hay todavía porcentajes de ahorro ni garantía de 30 FPS medidos.
