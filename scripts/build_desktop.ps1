$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Falta .venv. Consulta DESKTOP.md.' }
& $pythonExe -X utf8 -m unittest discover -s verification -p 'test_*.py'
if ($LASTEXITCODE -ne 0) { throw 'Las pruebas fallaron.' }
& $pythonExe -X utf8 -m PyInstaller --noconfirm EcoVision.spec
if ($LASTEXITCODE -ne 0) { throw 'No se pudo construir EcoVision.' }
& $pythonExe -X utf8 scripts/release_manifest.py
if ($LASTEXITCODE -ne 0) { throw 'No se pudo registrar la versión.' }
Write-Output 'Ejecutable: dist\EcoVision\EcoVision.exe. Distribuye la carpeta completa.'
