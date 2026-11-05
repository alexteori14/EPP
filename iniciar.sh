#!/usr/bin/env bash
# Arranca Vigía EPP con un comando: la API del motor (:8000) y el tablero Next.js (:3000).
#
#   ./iniciar.sh            # tablero en http://localhost:3000, API en :8000
#   ./iniciar.sh --build    # fuerza recompilación del tablero
#   PUERTO=3001 ./iniciar.sh
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOTOR="$RAIZ/motor-procesamiento"
TABLERO="$RAIZ/Frontend"
PYTHON="$MOTOR/.venv/bin/python"
API="http://127.0.0.1:8000"
PUERTO="${PUERTO:-3000}"
FORZAR_BUILD=0
[[ "${1:-}" == "--build" ]] && FORZAR_BUILD=1

aviso() { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
error() { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

[[ -x "$PYTHON" ]] || error "No se encontró $PYTHON. Consulta motor-procesamiento/README.md."
command -v npm >/dev/null || error "Falta Node.js/npm para ejecutar el tablero."
if ! grep -qsE '^(export )?(APIGEMINI|GEMINI_API_KEY)=.+' "$RAIZ/.env" 2>/dev/null; then
  aviso "Sin clave APIGEMINI en $RAIZ/.env: el Asistente IA usará el motor RAG determinista local (100% funcional offline)."
fi
if ss -ltn 2>/dev/null | grep -qE "[:.]$PUERTO\b"; then
  error "El puerto $PUERTO ya está ocupado. Usa otro: PUERTO=3001 ./iniciar.sh"
fi

PID_API=""
apagar() {
  if [[ -n "$PID_API" ]] && kill -0 "$PID_API" 2>/dev/null; then
    aviso "Apagando la API de Vigía EPP (:8000)"
    kill "$PID_API" 2>/dev/null || true
  fi
}
trap apagar EXIT
trap 'exit 130' INT TERM

if curl -sf -m 2 "$API/salud" >/dev/null; then
  aviso "La API del motor ya está corriendo en :8000; reutilizando instancia activa."
else
  aviso "Arrancando API del motor Vigía EPP en :8000"
  cd "$MOTOR"
  "$PYTHON" -m cruce.api > >(sed -u 's/^/[motor] /') 2>&1 &
  PID_API=$!
  for _ in $(seq 1 40); do
    curl -sf -m 1 "$API/salud" >/dev/null && break
    kill -0 "$PID_API" 2>/dev/null || error "La API no arrancó en :8000"
    sleep 0.25
  done
  curl -sf -m 1 "$API/salud" >/dev/null || error "La API no respondió después de 10 s"
fi

cd "$TABLERO"
if [[ ! -d node_modules ]]; then
  aviso "Instalando dependencias de Frontend (npm ci)"
  npm ci
fi
if [[ "$FORZAR_BUILD" == 1 || ! -f .next/BUILD_ID ]] ||
   [[ -n "$(find app components lib types public next.config.ts package.json tailwind.config.ts \
            -newer .next/BUILD_ID -print -quit 2>/dev/null)" ]]; then
  aviso "Compilando el tablero Next.js"
  npm run build
fi

aviso "Vigía EPP listo en http://localhost:$PUERTO   (Ctrl+C para apagar)"
npm start -- -p "$PUERTO"
