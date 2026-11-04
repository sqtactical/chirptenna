@echo off
rem Instalador de Chirptenna: doble clic. Descarga e instala lo necesario (sin permisos de administrador).
rem Opciones: instalar.bat -Comprobar   (solo dice que falta)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar\instalar.ps1" %*
echo.
pause
