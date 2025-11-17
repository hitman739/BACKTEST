#!/bin/bash

# Script para iniciar el Simulator de CopyTrading
# ================================================

echo "=================================================="
echo "🚀 INICIANDO SIMULADOR DE COPY TRADING"
echo "=================================================="

# Directorio base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$BASE_DIR/backend"
FRONTEND_DIR="$BASE_DIR/frontend"

# =====================================
# PASO 1: Arrancar Backend
# =====================================
echo ""
echo "📦 PASO 1: Arrancando Backend..."
cd "$BACKEND_DIR"

# Verificar si ya está corriendo
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Backend ya está corriendo en puerto 8000"
    echo "   Si quieres reiniciarlo, ejecuta: pkill -f 'python3 api_new'"
else
    echo "   Instalando dependencias del backend..."
    pip3 install -q -r requirements.txt 2>/dev/null

    echo "   Iniciando api_new.py en background..."
    nohup python3 api_new.py > /tmp/api_new.log 2>&1 &

    echo "   Esperando que el backend inicie..."
    sleep 5

    # Verificar que arrancó
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend corriendo en http://localhost:8000"
        echo "   Logs: tail -f /tmp/api_new.log"
    else
        echo "❌ Error: Backend no pudo arrancar"
        echo "   Revisa los logs: cat /tmp/api_new.log"
        exit 1
    fi
fi

# =====================================
# PASO 2: Arrancar Frontend
# =====================================
echo ""
echo "🎨 PASO 2: Arrancando Frontend..."
cd "$FRONTEND_DIR"

# Verificar si ya está corriendo
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Frontend ya está corriendo en puerto 5173"
else
    # Instalar dependencias si no existen
    if [ ! -d "node_modules" ]; then
        echo "   Instalando dependencias de Node.js (esto puede tardar)..."
        npm install
    else
        echo "   Dependencias ya instaladas ✓"
    fi

    echo "   Iniciando Vite dev server..."
    nohup npm run dev > /tmp/vite.log 2>&1 &

    echo "   Esperando que el frontend inicie..."
    sleep 8

    # Verificar que arrancó
    if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "✅ Frontend corriendo en http://localhost:5173"
        echo "   Logs: tail -f /tmp/vite.log"
    else
        echo "⚠️  Frontend tardando en arrancar, revisa /tmp/vite.log"
    fi
fi

# =====================================
# RESUMEN
# =====================================
echo ""
echo "=================================================="
echo "✅ SIMULADOR LISTO"
echo "=================================================="
echo ""
echo "📊 URLs Disponibles:"
echo "   • Frontend:  http://localhost:5173"
echo "   • Backend:   http://localhost:8000"
echo "   • API Docs:  http://localhost:8000/docs"
echo ""
echo "🔧 Rutas del Frontend:"
echo "   • Home:        http://localhost:5173/"
echo "   • Simulator:   http://localhost:5173/simulator"
echo "   • SimulatorV2: http://localhost:5173/simulator-v2"
echo ""
echo "🛑 Para detener:"
echo "   pkill -f 'python3 api_new'"
echo "   pkill -f 'vite'"
echo ""
echo "📋 Ver logs:"
echo "   Backend:  tail -f /tmp/api_new.log"
echo "   Frontend: tail -f /tmp/vite.log"
echo ""
echo "=================================================="
