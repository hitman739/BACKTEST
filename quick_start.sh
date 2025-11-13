#!/bin/bash
# Quick Start Script para Vault Reverse Engineering

echo "=========================================================================="
echo "🎯 VAULT REVERSE ENGINEERING - QUICK START"
echo "=========================================================================="
echo ""

# Check if vault address provided
if [ -z "$1" ]; then
    echo "❌ Error: No vault address provided"
    echo ""
    echo "Usage:"
    echo "  ./quick_start.sh <vault_address> [symbol] [timeframe]"
    echo ""
    echo "Example:"
    echo "  ./quick_start.sh 0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b HYPE 5m"
    echo ""
    exit 1
fi

VAULT_ADDRESS=$1
SYMBOL=${2:-HYPE}
TIMEFRAME=${3:-5m}

echo "📋 Configuration:"
echo "   Vault: $VAULT_ADDRESS"
echo "   Symbol: $SYMBOL"
echo "   Timeframe: $TIMEFRAME"
echo ""

# Step 1: Run analysis
echo "=========================================================================="
echo "STEP 1: Running complete vault analysis..."
echo "=========================================================================="
python3 reverse_engineer_vault_complete.py \
    --vault $VAULT_ADDRESS \
    --symbol $SYMBOL \
    --timeframe $TIMEFRAME

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Analysis failed. Check error messages above."
    exit 1
fi

echo ""
echo "✅ Analysis complete!"
echo ""

# Get vault short ID
VAULT_ID=$(echo $VAULT_ADDRESS | cut -c1-10)

# Step 2: Show where files are
echo "=========================================================================="
echo "STEP 2: Generated files location"
echo "=========================================================================="
echo ""
echo "📁 Output directory: reports/reverse_engineering/$VAULT_ID/"
echo ""
echo "Key files:"
echo "  • strategy_summary.txt         - Human-readable strategy rules"
echo "  • extracted_rules.json         - Precise rules for implementation"
echo "  • pattern_analysis_complete.json - ML analysis results"
echo "  • validation_report.txt        - Performance metrics"
echo "  • MASTER_REPORT.json          - Complete analysis"
echo ""

# Step 3: Show strategy summary
echo "=========================================================================="
echo "STEP 3: Strategy Summary (Quick View)"
echo "=========================================================================="
echo ""

if [ -f "reports/reverse_engineering/$VAULT_ID/strategy_summary.txt" ]; then
    cat "reports/reverse_engineering/$VAULT_ID/strategy_summary.txt"
else
    echo "⚠️  Strategy summary not found"
fi

echo ""
echo "=========================================================================="
echo "NEXT STEPS"
echo "=========================================================================="
echo ""
echo "1️⃣  Review the strategy summary above"
echo ""
echo "2️⃣  Check detailed rules:"
echo "    cat reports/reverse_engineering/$VAULT_ID/extracted_rules.json"
echo ""
echo "3️⃣  Read the step-by-step guide:"
echo "    cat PASO_A_PASO_VAULT_ANALYSIS.md"
echo ""
echo "4️⃣  Implement strategy in strategies/vault_clone_${SYMBOL,,}.py"
echo ""
echo "5️⃣  Run backtest and compare results"
echo ""
echo "📖 For detailed instructions, see: PASO_A_PASO_VAULT_ANALYSIS.md"
echo ""
echo "=========================================================================="
