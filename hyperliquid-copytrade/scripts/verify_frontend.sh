#!/bin/bash

# Script de verificación del frontend
# ====================================

echo "🔍 Verificando configuración del frontend..."
echo ""

cd "$(dirname "$0")/../frontend"

# Verificar archivos de configuración
echo "📋 Verificando archivos de configuración:"
FILES=("package.json" "vite.config.js" "tailwind.config.js" "postcss.config.js" "index.html" "src/main.jsx" "src/index.css")

ALL_FOUND=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - NOT FOUND"
        ALL_FOUND=false
    fi
done

echo ""

if [ "$ALL_FOUND" = false ]; then
    echo "❌ Algunos archivos de configuración faltan."
    exit 1
fi

# Verificar dependencias
echo "📦 Verificando dependencias:"
if [ -d "node_modules" ]; then
    echo "  ✅ node_modules existe"
else
    echo "  ⚠️  node_modules no existe. Ejecutando npm install..."
    npm install
    if [ $? -eq 0 ]; then
        echo "  ✅ npm install completado"
    else
        echo "  ❌ npm install falló"
        exit 1
    fi
fi

echo ""

# Verificar que Tailwind CSS esté en package.json
echo "🎨 Verificando Tailwind CSS:"
if grep -q "tailwindcss" package.json; then
    echo "  ✅ tailwindcss en package.json"
else
    echo "  ❌ tailwindcss NO está en package.json"
    exit 1
fi

if grep -q "postcss" package.json; then
    echo "  ✅ postcss en package.json"
else
    echo "  ❌ postcss NO está en package.json"
    exit 1
fi

if grep -q "autoprefixer" package.json; then
    echo "  ✅ autoprefixer en package.json"
else
    echo "  ❌ autoprefixer NO está en package.json"
    exit 1
fi

echo ""

# Verificar directivas de Tailwind en CSS
echo "🎨 Verificando directivas de Tailwind en src/index.css:"
if grep -q "@tailwind base" src/index.css && \
   grep -q "@tailwind components" src/index.css && \
   grep -q "@tailwind utilities" src/index.css; then
    echo "  ✅ Directivas de Tailwind presentes"
else
    echo "  ❌ Faltan directivas de Tailwind en src/index.css"
    exit 1
fi

echo ""

# Test de build
echo "🏗️  Probando build del proyecto:"
timeout 15 npm run dev > /tmp/vite_test.log 2>&1 &
VITE_PID=$!

sleep 5

if ps -p $VITE_PID > /dev/null; then
    echo "  ✅ Vite dev server arrancó correctamente"
    kill $VITE_PID 2>/dev/null
    wait $VITE_PID 2>/dev/null
else
    echo "  ❌ Vite dev server falló al arrancar"
    cat /tmp/vite_test.log
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ FRONTEND CONFIGURADO CORRECTAMENTE"
echo "=================================================="
echo ""
echo "Para arrancar el frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "URL: http://localhost:5173"
echo ""
