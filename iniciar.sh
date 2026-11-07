#!/usr/bin/env bash
# Arranca Vigía EPP con un solo comando desde un repositorio recién descargado:
#   1. Crea .env desde .env.example si no existe
#   2. Crea motor-procesamiento/.venv e instala dependencias Python si faltan
#   3. Sincroniza artefactos base de demostración
#   4. Levanta la API del motor (:8000)
#   5. Instala node_modules, compila Next.js si hace falta y levanta el tablero (:3000)
#
# Uso:
#   ./iniciar.sh              # Arranca todo en http://localhost:3000 (o siguiente puerto libre)
#   ./iniciar.sh --build      # Fuerza recompilación del tablero Next.js
#   ./iniciar.sh --verificar  # Verifica instalación, API (:8000) y build de Frontend y termina (CI/test)
#   PUERTO=3001 ./iniciar.sh  # Usa un puerto específico para el Frontend
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOTOR="$RAIZ/motor-procesamiento"
TABLERO="$RAIZ/Frontend"
API_PORT="${API_PORT:-8000}"
API="http://127.0.0.1:$API_PORT"
PUERTO_DEFINIDO="${PUERTO:-}"
PUERTO="${PUERTO:-3000}"
FORZAR_BUILD=0
SOLO_VERIFICAR=0

for arg in "$@"; do
  case "$arg" in
    --build) FORZAR_BUILD=1 ;;
    --verificar|--check) SOLO_VERIFICAR=1 ;;
  esac
done

aviso() { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
exito() { printf '\033[1;32m✓ %s\033[0m\n' "$*"; }
error() { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# 1. Detectar ejecutable de Python del sistema (para bootstrap si aún no existe .venv)
SYS_PYTHON=""
for cand in python3.12 python3.11 python3.10 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    SYS_PYTHON="$cand"
    break
  fi
done
[[ -n "$SYS_PYTHON" ]] || error "No se encontró Python 3 instalado en el sistema. Instala Python 3.10+ y vuelve a intentar."

command -v npm >/dev/null 2>&1 || error "Falta Node.js/npm para ejecutar el tablero. Instala Node.js 18.18+ (recomendado Node 20 LTS)."

# 2. Crear .env automáticamente desde .env.example si no existe
if [[ ! -f "$RAIZ/.env" && -f "$RAIZ/.env.example" ]]; then
  cp "$RAIZ/.env.example" "$RAIZ/.env"
  aviso "Archivo .env creado automáticamente a partir de .env.example."
fi
if ! grep -qsE '^(export )?(APIGEMINI|GEMINI_API_KEY)=.+' "$RAIZ/.env" 2>/dev/null; then
  aviso "Sin clave APIGEMINI en .env: el Asistente IA usará el motor RAG determinista local (100% funcional offline)."
fi

# 3. Resolver o crear automáticamente el entorno virtual en motor-procesamiento/.venv
resolver_venv_python() {
  if [[ -x "$MOTOR/.venv/bin/python" ]]; then
    echo "$MOTOR/.venv/bin/python"
  elif [[ -x "$MOTOR/.venv/Scripts/python.exe" ]]; then
    echo "$MOTOR/.venv/Scripts/python.exe"
  else
    echo ""
  fi
}

PYTHON="$(resolver_venv_python)"
if [[ -z "$PYTHON" ]]; then
  aviso "Primera ejecución detectada: creando entorno virtual en motor-procesamiento/.venv..."
  if command -v uv >/dev/null 2>&1; then
    uv venv "$MOTOR/.venv"
  else
    "$SYS_PYTHON" -m venv "$MOTOR/.venv" || error "No se pudo crear .venv. En Ubuntu/Debian ejecuta: sudo apt install python3-venv"
  fi
  PYTHON="$(resolver_venv_python)"
fi

[[ -n "$PYTHON" ]] || error "No se pudo localizar el intérprete dentro de $MOTOR/.venv."

# Comprobar que los paquetes esenciales del motor estén instalados en .venv
if ! "$PYTHON" -c "import cv2, numpy, ultralytics, supervision" >/dev/null 2>&1; then
  aviso "Instalando dependencias de Python en motor-procesamiento/.venv..."
  if command -v uv >/dev/null 2>&1; then
    uv pip install --python "$PYTHON" -r "$MOTOR/requirements.txt" || {
      aviso "Reintentando instalación en modo compatible CPU/multiplataforma..."
      grep -vE '^(onnxruntime-gpu|nvidia-curand)' "$MOTOR/requirements.txt" > "$MOTOR/.requirements-cpu.tmp"
      uv pip install --python "$PYTHON" -r "$MOTOR/.requirements-cpu.tmp" onnxruntime
      rm -f "$MOTOR/.requirements-cpu.tmp"
    }
  else
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install -r "$MOTOR/requirements.txt" || {
      aviso "Reintentando instalación en modo compatible CPU/multiplataforma..."
      grep -vE '^(onnxruntime-gpu|nvidia-curand)' "$MOTOR/requirements.txt" > "$MOTOR/.requirements-cpu.tmp"
      "$PYTHON" -m pip install -r "$MOTOR/.requirements-cpu.tmp" onnxruntime
      rm -f "$MOTOR/.requirements-cpu.tmp"
    }
  fi
  exito "Dependencias de Python instaladas correctamente."
fi

# 4. Asegurar carpetas base de salida para modo demo tras clonar
mkdir -p "$MOTOR/salida" "$MOTOR/analisis"
if [[ ! -f "$MOTOR/salida/hallazgos.json" && -f "$TABLERO/public/salida/hallazgos.json" ]]; then
  cp "$TABLERO/public/salida/hallazgos.json" "$MOTOR/salida/hallazgos.json"
fi

# Funciones auxiliares multiplataforma en Python (sin depender de ss ni curl)
puerto_ocupado() {
  "$PYTHON" - "$1" <<'PY'
import socket, sys
port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(0.3)
    sys.exit(0 if s.connect_ex(("127.0.0.1", port)) == 0 else 1)
PY
}

api_saludable() {
  "$PYTHON" - "$API/salud" <<'PY'
import sys, urllib.request
try:
    with urllib.request.urlopen(sys.argv[1], timeout=1.5) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
PY
}

# 5. Seleccionar puerto libre para el Frontend (:3000 o siguiente disponible si está ocupado)
if puerto_ocupado "$PUERTO"; then
  if [[ -n "$PUERTO_DEFINIDO" ]]; then
    error "El puerto $PUERTO ya está ocupado. Usa otro: PUERTO=3001 ./iniciar.sh"
  fi
  while puerto_ocupado "$PUERTO"; do
    PUERTO=$((PUERTO + 1))
  done
  aviso "El puerto 3000 estaba en uso; se usará automáticamente el puerto libre $PUERTO."
fi

PID_API=""
apagar() {
  if [[ -n "$PID_API" ]] && kill -0 "$PID_API" 2>/dev/null; then
    aviso "Apagando la API de Vigía EPP (:$API_PORT)"
    kill "$PID_API" 2>/dev/null || true
  fi
}
trap apagar EXIT
trap 'exit 130' INT TERM

# 6. Arrancar o reutilizar la API del motor (:8000)
if api_saludable; then
  aviso "La API del motor ya está corriendo en :$API_PORT; reutilizando instancia activa."
else
  aviso "Arrancando API del motor Vigía EPP en :$API_PORT"
  (
    cd "$MOTOR"
    exec "$PYTHON" -m cruce.api --puerto "$API_PORT"
  ) > >(sed -u 's/^/[motor] /') 2>&1 &
  PID_API=$!
  for _ in $(seq 1 60); do
    api_saludable && break
    kill -0 "$PID_API" 2>/dev/null || error "La API no pudo arrancar en :$API_PORT"
    sleep 0.25
  done
  api_saludable || error "La API no respondió en :$API_PORT después de 15 s"
fi

# 7. Instalar dependencias de Frontend y compilar Next.js si hace falta
cd "$TABLERO"
if [[ ! -d node_modules || ! -e node_modules/.bin/next ]]; then
  aviso "Instalando dependencias de Frontend (npm ci / npm install)..."
  npm ci || npm install
fi

if [[ "$FORZAR_BUILD" == 1 || ! -f .next/BUILD_ID ]] ||
   [[ -n "$(find app components lib types public next.config.ts package.json tailwind.config.ts \
            -newer .next/BUILD_ID -print -quit 2>/dev/null)" ]]; then
  aviso "Compilando el tablero Next.js..."
  npm run build
fi

if [[ "$SOLO_VERIFICAR" == 1 ]]; then
  exito "Verificación completa: entorno Python (.venv), API (:8000) y compilación de Frontend listos."
  exit 0
fi

exito "Vigía EPP listo en http://localhost:$PUERTO   (Ctrl+C para apagar)"
npm start -- -p "$PUERTO"
