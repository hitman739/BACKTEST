#!/bin/bash

echo "🛑 Deteniendo Simulador de Copy Trading..."

# Detener backend
if pgrep -f "python3 api_new" > /dev/null; then
    echo "   Deteniendo backend..."
    pkill -f "python3 api_new"
    echo "   ✅ Backend detenido"
else
    echo "   ℹ️  Backend no estaba corriendo"
fi

# Detener frontend
if pgrep -f "vite" > /dev/null; then
    echo "   Deteniendo frontend..."
    pkill -f "vite"
    echo "   ✅ Frontend detenido"
else
    echo "   ℹ️  Frontend no estaba corriendo"
fi

echo ""
echo "✅ Todos los servicios detenidos"
