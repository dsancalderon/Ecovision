# Recursos de interfaz

Las imágenes originales se conservan. La interfaz consume:

- `static/images/earth_eco_globe_clean.png`
- `static/images/green_bin_graphic_clean.png`

Se generaron mediante la herramienta integrada imagegen, como ediciones de los
PNG originales. Ambos archivos se verificaron como RGBA con alfa entre 0 y 255
y se inspeccionaron en la interfaz renderizada.

Prompts utilizados:

> Use case: background-extraction. Edit the supplied EcoVision earth illustration: remove only the entire baked-in gray-and-white checkerboard background, including spaces between the leaves, replacing it with actual transparent alpha. Preserve the globe, every leaf, pastel green/mint palette, contours, composition, and appearance as closely as possible. Output one transparent PNG, square. No checkerboard, no solid background, no added elements. This is a production UI asset.

> Use case: background-extraction. Edit supplied recycling bin asset: remove only the baked-in gray/white checkerboard background completely, use actual transparent alpha. Preserve the dark green bin illustration, edges, white recycling symbol, word RECYCLING and composition. Transparent PNG with clean edges, no checkerboard, no solid background, no new elements. Production UI cutout.

## Video PET

El archivo `static/videos/botella_plastica_pet.mp4` es una copia del video facilitado
por el usuario en Downloads (`el_la_etiqueta_pon_el_logo_de.mp4`). Se conserva completo,
720×1280, 24 FPS, 10 segundos; no se recortó ni recodificó. El póster JPEG de 288×512
se extrajo del primer frame. No se generan nuevos renders dentro de la aplicación.

Los SVG del HTML son ilustraciones estáticas de respaldo. Lata, cartón, Tetra Pak,
vidrio y residuo no aprovechable aún no tienen videos proporcionados.

## Verificación

`check-ui.cjs` requiere Playwright, Microsoft Edge y Flask en `http://127.0.0.1:5055`:

```powershell
python -X utf8 -c "from realtime_ui_app import app; app.run(host='127.0.0.1', port=5055, debug=False, threaded=True, use_reloader=False)"
node verification/check-ui.cjs
```

Resultados actuales en `results.json`; capturas con prefijo `video-`.
`video-preview.html` conserva el diseño real de la tarjeta y reproduce el MP4 en
bucle para inspección. No tiene detección ni cuenta regresiva funcional.
La captura `idle.png` es histórica y corresponde a la pantalla inicial.
No se han medido cámara física, inferencia YOLO ni rendimiento con ambas activas.
