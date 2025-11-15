#!/bin/bash
# Setup script - Instala todas las dependencias

echo "🚀 Instalando Hyperliquid CopyTrading..."
echo ""

# Check if we're in the right directory
if [ ! -f "setup.sh" ]; then
    echo "❌ Error: Ejecuta este script desde la carpeta hyperliquid-copytrade/"
    exit 1
fi

# Install Backend
echo "📦 Instalando Backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..
echo "✅ Backend instalado"
echo ""

# Install Frontend
echo "📦 Instalando Frontend..."
cd frontend
npm install
cd ..
echo "✅ Frontend instalado"
echo ""

echo "🎉 Instalación completa!"
echo ""
echo "Para ejecutar la app:"
echo "  ./start-backend.sh   (en una terminal)"
echo "  ./start-frontend.sh  (en otra terminal)"
echo ""
echo "O lee QUICKSTART.md para más detalles"
