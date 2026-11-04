@echo off
rem Abre Chirptenna: arranca la interfaz y el navegador en http://localhost:8080
setlocal
set "PY=%LOCALAPPDATA%\antenas\venv\Scripts\python.exe"
if not exist "%PY%" (
    echo Chirptenna no esta instalado: ejecuta primero instalar.bat
    pause
    exit /b 1
)
cd /d "%~dp0"
set CHIRPTENNA_ABRIR=1
set PYTHONIOENCODING=utf-8
echo Chirptenna en http://localhost:8080
echo Deja esta ventana abierta mientras lo usas; cierrala para apagar el programa.
echo.
"%PY%" gui\app.py
if errorlevel 1 (
    echo.
    echo El programa se ha cerrado con un error. Si ya estaba abierto en otra ventana,
    echo usa esa: http://localhost:8080
    start "" http://localhost:8080
    pause
)
