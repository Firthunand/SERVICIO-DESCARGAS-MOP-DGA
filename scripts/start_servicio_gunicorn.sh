#!/bin/bash
# Script de arranque del servicio de descargas MOP DGA usando Gunicorn
# Ejecutar desde la raíz del proyecto: ./scripts/start_servicio_gunicorn.sh

set -e
cd "$(dirname "$0")/.."
PROYECTO_ROOT="$(pwd)"
DISPLAY_NUM=99
XVFB_PID=""
OPENBOX_PID=""
VNC_PID=""

cleanup() {
  echo ""
  echo "Deteniendo servicios..."
  [ -n "$VNC_PID" ] && kill "$VNC_PID" 2>/dev/null || true
  [ -n "$OPENBOX_PID" ] && kill "$OPENBOX_PID" 2>/dev/null || true
  [ -n "$XVFB_PID" ] && kill "$XVFB_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

# 1. Xvfb (pantalla virtual)
if [ -f "/tmp/.X${DISPLAY_NUM}-lock" ]; then
  echo "Display :${DISPLAY_NUM} ya en uso (Xvfb corriendo)."
else
  Xvfb ":${DISPLAY_NUM}" -screen 0 1920x1080x24 &
  XVFB_PID=$!
  sleep 2
  echo "Xvfb iniciado en display :${DISPLAY_NUM} (PID $XVFB_PID)"
fi

export DISPLAY=":${DISPLAY_NUM}"

# 2. Openbox (gestor de ventanas)
if command -v openbox >/dev/null 2>&1; then
  openbox &
  OPENBOX_PID=$!
  sleep 1
  echo "Openbox iniciado (PID $OPENBOX_PID)"
else
  echo "AVISO: openbox no instalado. Instalar con: sudo apt install openbox"
fi

# 3. x11vnc (para noVNC)
if command -v x11vnc >/dev/null 2>&1; then
  x11vnc -display ":$DISPLAY_NUM" -forever -shared -rfbport 5900 -noxdamage &
  VNC_PID=$!
  sleep 1
  echo "x11vnc escuchando en puerto 5900 (PID $VNC_PID)"
else
  echo "AVISO: x11vnc no instalado. Instalar con: sudo apt install x11vnc"
fi

# 4. Gunicorn (entorno virtual si existe)
echo ""
echo "Iniciando aplicación con Gunicorn en $PROYECTO_ROOT"
if [ -d "$PROYECTO_ROOT/env" ]; then
  . "$PROYECTO_ROOT/env/bin/activate"
fi

# Usar run_flask:app como entrypoint WSGI
exec gunicorn --workers 3 --bind 0.0.0.0:5000 run_flask:app

