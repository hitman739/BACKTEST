#!/bin/bash
# Backtest Multi-Pair en Mac - Script Todo-en-Uno
# Descarga datos + ejecuta backtest automáticamente

echo "======================================================================"
echo "🚀 BACKTEST MULTI-PAIR - TETR STRATEGY"
echo "======================================================================"
echo ""
echo "Este script va a:"
echo "  1. Descargar datos de Binance (BTC, ETH, SOL)"
echo "  2. Ejecutar backtest en 15m timeframe"
echo "  3. Mostrar resultados comparativos"
echo ""
echo "Período: Últimos 60 días"
echo "Pairs: BTCUSDT, ETHUSDT, SOLUSDT"
echo "Timeframe: 15m"
echo ""
echo "======================================================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "   Instala Python 3.9+ desde https://www.python.org/"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"
echo ""

# Verificar dependencias
echo "🔍 Verificando dependencias..."
python3 -c "import pandas, numpy, aiohttp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Instalando dependencias faltantes..."
    pip3 install pandas numpy aiohttp ccxt -q
    if [ $? -ne 0 ]; then
        echo "❌ Error instalando dependencias"
        exit 1
    fi
fi
echo "✅ Dependencias OK"
echo ""

# Paso 1: Descargar datos
echo "======================================================================"
echo "📥 PASO 1: DESCARGANDO DATOS DE BINANCE"
echo "======================================================================"
echo ""

python3 prepare_data.py

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Error descargando datos"
    echo ""
    echo "Opciones:"
    echo "  1. Verifica tu conexión a internet"
    echo "  2. Usa VPN si Binance está bloqueado"
    echo "  3. Ejecuta manualmente: python3 prepare_data.py"
    echo ""
    read -p "¿Continuar con datos existentes? (y/n): " continue
    if [ "$continue" != "y" ]; then
        echo "Abortando..."
        exit 1
    fi
fi

echo ""
echo "Esperando 3 segundos..."
sleep 3

# Paso 2: Ejecutar backtest
echo ""
echo "======================================================================"
echo "🧪 PASO 2: EJECUTANDO BACKTEST"
echo "======================================================================"
echo ""

python3 backtest_multi_pairs.py

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "✅ BACKTEST COMPLETADO EXITOSAMENTE"
    echo "======================================================================"
    echo ""
    echo "📊 Resultados guardados en:"
    echo "   reports/tetr_*_15m_*/"
    echo ""
    echo "📈 Para ver trades detallados:"
    echo "   cat reports/tetr_BTCUSDT_15m_*/trades.csv"
    echo ""
    echo "🔄 Para correr de nuevo:"
    echo "   ./run_mac_backtest.sh"
    echo ""
else
    echo ""
    echo "======================================================================"
    echo "❌ ERROR EN BACKTEST"
    echo "======================================================================"
    echo ""
    echo "Revisa los errores arriba y:"
    echo "  1. Verifica que los datos estén descargados"
    echo "  2. Ejecuta manualmente: python3 backtest_multi_pairs.py"
    echo "  3. Revisa RUN_ON_MAC.md para troubleshooting"
    echo ""
    exit 1
fi
