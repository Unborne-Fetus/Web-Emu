@echo off
setlocal
cd /d "%~dp0"
title Web Emu - Offline
if not exist "runtime\node.exe" (
  echo ERROR: The offline launcher is incomplete.
  echo.
  echo Download the "Web-Emu-Offline-All-Systems" artifact from GitHub Actions,
  echo extract the ENTIRE ZIP, then double-click this file again.
  echo Do not download Start-Web-Emu.cmd by itself.
  echo.
  pause
  exit /b 1
)
if not exist "vendor\emulatorjs\data\cores\azahar-thread-wasm.data" (
  echo ERROR: The Azahar 3DS emulator core is missing.
  echo Please extract the complete ZIP before launching.
  pause
  exit /b 1
)
echo Launching Web Emu offline...
"runtime\node.exe" "scripts\offline-server.cjs"
if errorlevel 1 (
  echo.
  echo Web Emu could not start. Read the error above.
  pause
)
endlocal
