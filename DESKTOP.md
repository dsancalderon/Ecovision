# EcoVision Desktop 0.2.0

## Abrir y seguir desarrollando

Haz doble clic en **EcoVision Desarrollo.vbs**, en la raíz del proyecto. No necesitas escribir comandos. Este acceso utiliza el código actual de esta carpeta y el intérprete de `.venv`. No es la aplicación que se distribuye a otros computadores.

- HTML, CSS, JavaScript y plantillas: la ventana detecta cambios y recarga automáticamente. También tienes «Recargar».
- Archivos Python de la raíz: se cierra la ventana, se libera el motor y el lanzador la vuelve a abrir con el código nuevo. También tienes «Reiniciar motor».
- Cambios en dependencias: hay que instalarlas en el entorno y reiniciar.
- Al recargar o reiniciar se reinicia la prueba en curso. Un reinicio del motor vuelve al menú.
- Si el código tiene un error de sintaxis, el lanzador muestra dónde consultar `development.log`. Corrige el error y vuelve a abrir el acceso.
- Este entorno se preparó reutilizando las bibliotecas Python ya instaladas en este equipo. Si mueves el proyecto a otro equipo, prepara su entorno de nuevo.

Preparación en un equipo de desarrollo nuevo (requiere Python e internet para descargar dependencias):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
```

Las dependencias de ejecución usadas para cada distribución quedan registradas en `release.json`. `requirements.txt` conserva los límites existentes; no equivale a un bloqueo exacto de versiones.

## Aplicación para usar o distribuir

En **dist/EcoVision**, abre **EcoVision.exe**. Conserva la carpeta completa junto con `EcoVision.pkg` y `_internal`; el ejecutable solo no contiene todos los archivos. El código se guarda en un paquete separado para evitar reescribir un ejecutable grande durante cada actualización. No necesita Python instalado ni acceso al código fuente.

Puedes copiar esa carpeta a una memoria USB. Para instalarla en el perfil de Windows, ejecuta **Instalar EcoVision.vbs** dentro de esa carpeta. Copia la versión a `%LOCALAPPDATA%\Programs\EcoVision\0.2.0` y crea accesos en Escritorio y el menú Inicio. No sobrescribe una instalación de la misma versión. Cierra la aplicación antes de gestionar sus archivos.

Windows debe disponer de WebView2. El paquete incluye el instalador oficial completo x64 en `dependencies/MicrosoftEdgeWebView2RuntimeInstallerX64.exe`, cuya firma de Microsoft se verificó. El instalador de EcoVision lo ejecuta antes de copiar la aplicación para preparar ese prerrequisito sin internet. Se verificó la ventana nativa en este equipo; queda pendiente instalar en un Windows limpio sin Python ni WebView2. Esta distribución corresponde a Windows x64.

## Modos

El arranque muestra logo y barra por etapas, después el menú principal con el logo centrado. La ventana de inicio se ajusta al formulario y aparece en el centro de la pantalla, sin scroll ni maximización. Al entrar a Simulación o Prueba Real se activa pantalla completa; al volver al menú se desactiva y se recupera la ventana compacta centrada. Inicialmente no se abre cámara ni se carga YOLO. El selector de cámaras está integrado en el componente de Prueba Real.

- **Simulación:** cámara desactivada, sin modelo, visor visible con «Cámara desactivada» y controles de materiales abajo a la derecha. La confianza mostrada es simulada.
- **Prueba real:** carga del modelo local y apertura del índice de cámara seleccionado. No muestra controles de simulación; los disparadores de simulación también están bloqueados en la lógica. Si no hay imágenes o no carga el modelo, ofrece volver a elegir modo.
- **Menú principal:** finaliza la sesión, libera la cámara y permite elegir nuevamente.

El menú muestra las cámaras disponibles con sus nombres de Windows mediante DirectShow, sin abrir sus transmisiones para enumerarlas. Si no hay cámaras, se deshabilita Prueba Real. Se utiliza la cámara elegida, sin cambiar silenciosamente a otra.

## Modelo provisional

El `model/best.pt` actual contiene **botella_reciclable** y **carton**. Es una cobertura temporal de dos clases. La interfaz de simulación tiene seis materiales, lo cual no significa que el modelo los reconozca. La aplicación lee las clases del peso cargado y las muestra en prueba real.

Para probar un peso nuevo en Desarrollo: reemplaza `model/best.pt`, vuelve al menú e inicia otra prueba real. No necesitas reconstruir el ejecutable de desarrollo.

Para sustituir el modelo de la aplicación distribuida sin reconstruirla, coloca un peso compatible en `%LOCALAPPDATA%\EcoVision\models\best.pt`. Este archivo tiene prioridad sobre el incluido. Vuelve al menú y entra en prueba real para cargarlo. Para regresar al peso incluido, retira ese archivo con la app cerrada. Un formato o arquitectura que requiera bibliotecas nuevas sí puede exigir actualizar el programa.

No se descarga un modelo de respaldo: si falta el modelo local, se muestra un error. YOLO funciona en modo offline y con instalación automática de dependencias desactivada.

## Datos y versiones

Configuración, registros y datos del motor: `%LOCALAPPDATA%\EcoVision`. `settings.json` conserva la cámara elegida. `development.log` registra la ejecución desde el lanzador; `ecovision.log` permite revisar el arranque de la aplicación sin consola.

`desktop_runtime.py` define la versión de la aplicación. El paquete lleva `release.json`, con versión, hash del código, hash SHA-256 del modelo, clases y versiones de dependencias. Para publicar otra versión cambia `VERSION`, genera el paquete y verifica sus diagnósticos. El número del instalador se genera desde esa misma versión.

La aplicación instalada no lee los cambios de tu carpeta de desarrollo. Para publicar cambios de Python o dependencias se genera otra distribución; para trabajar diariamente utiliza EcoVision Desarrollo.

No se implementó todavía un servicio de actualizaciones por internet ni un importador de paquetes desde el menú. Es la fase posterior del plan. Por ahora las versiones se distribuyen como carpetas completas y el modelo puede sustituirse localmente como se indica arriba. Funcionar offline no impide actualizar, pero los archivos nuevos deben llegar por internet, red local o USB.

## Construir y verificar

```powershell
powershell -File scripts/build_desktop.ps1
.\.venv\Scripts\python.exe -m unittest discover -s verification -p 'test_*.py'
.\.venv\Scripts\python.exe verification/smoke_desktop_native.py
```

Diagnóstico de la distribución, sin cámara, con conexiones de red bloqueadas durante la prueba:

```powershell
.\dist\EcoVision\EcoVision.exe --diagnostics C:\ruta\diagnostico.json
```

El diagnóstico carga el peso y ejecuta inferencia sobre una imagen sintética. No mide exactitud de clasificación ni sustituye pruebas físicas de cámara, materiales e iluminación.

Los resultados de interfaz están en `verification/desktop-browser-results.json` y `verification/desktop-native-results.json`. La prueba del navegador bloquea recursos externos y verifica la reproducción de PET y cartón. Las pruebas de transición con cámara simulada verifican liberación, aislamiento, errores y recuperación; deben complementarse con hardware real.
