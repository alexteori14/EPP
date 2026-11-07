@echo off
setlocal
REM Lanzador de 1 comando para Windows (CMD / PowerShell / Doble clic)
REM Si Git Bash o WSL está disponible, delega a iniciar.sh; si no, ejecuta los pasos nativamente.

cd /d "%~dp0"

where bash >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    bash ./iniciar.sh %*
    exit /b %ERRORLEVEL%
)

echo [Vigia EPP] Iniciando en Windows nativo...
if not exist ".env" (
    if exist ".env.example" copy /Y ".env.example" ".env" >nul
)

if not exist "motor-procesamiento\.venv\Scripts\python.exe" (
    echo [Vigia EPP] Creando entorno virtual en motor-procesamiento\.venv...
    python -m venv "motor-procesamiento\.venv"
)

"motor-procesamiento\.venv\Scripts\python.exe" -c "import cv2, numpy, ultralytics, supervision" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [Vigia EPP] Instalando dependencias de Python...
    "motor-procesamiento\.venv\Scripts\python.exe" -m pip install --upgrade pip
    "motor-procesamiento\.venv\Scripts\python.exe" -m pip install -r "motor-procesamiento\requirements.txt"
)

start "Vigia EPP Motor API" /B cmd /c "cd /d motor-procesamiento && .venv\Scripts\python.exe -m cruce.api --puerto 8000"

cd /d "Frontend"
if not exist "node_modules\.bin\next.cmd" (
    echo [Vigia EPP] Instalando dependencias de Frontend...
    call npm ci || call npm install
)
if not exist ".next\BUILD_ID" (
    echo [Vigia EPP] Compilando tablero Next.js...
    call npm run build
)

echo [Vigia EPP] Listo en http://localhost:3000
call npm start -- -p 3000
