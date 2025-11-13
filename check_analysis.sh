#!/bin/bash
# Check if vault analysis completed successfully

if [ -z "$1" ]; then
    echo "Usage: ./check_analysis.sh <vault_short_id>"
    echo "Example: ./check_analysis.sh 0x9b55c8c9"
    exit 1
fi

VAULT_ID=$1
DIR="reports/reverse_engineering/$VAULT_ID"

echo "=========================================================================="
echo "🔍 CHECKING ANALYSIS RESULTS FOR VAULT: $VAULT_ID"
echo "=========================================================================="
echo ""

# Check if directory exists
if [ ! -d "$DIR" ]; then
    echo "❌ Analysis directory not found: $DIR"
    echo ""
    echo "Run analysis first:"
    echo "  ./quick_start.sh <vault_address> <symbol> <timeframe>"
    exit 1
fi

echo "✅ Analysis directory exists: $DIR"
echo ""

# Check required files
echo "📄 Checking required files..."
echo ""

FILES=(
    "MASTER_REPORT.json:Master report with all data"
    "extracted_rules.json:Precise trading rules"
    "strategy_summary.txt:Human-readable strategy"
    "pattern_analysis_complete.json:ML analysis results"
    "validation_report.json:Performance validation"
    "validation_report.txt:Validation text report"
    "positions_with_features.parquet:Full dataset"
    "positions.parquet:Basic positions"
    "feature_summary.csv:Feature statistics"
)

ALL_GOOD=true

for file_desc in "${FILES[@]}"; do
    IFS=':' read -r file desc <<< "$file_desc"
    if [ -f "$DIR/$file" ]; then
        size=$(du -h "$DIR/$file" | cut -f1)
        echo "  ✅ $file ($size) - $desc"
    else
        echo "  ❌ MISSING: $file - $desc"
        ALL_GOOD=false
    fi
done

echo ""

if [ "$ALL_GOOD" = true ]; then
    echo "=========================================================================="
    echo "✅ ALL FILES PRESENT - Analysis completed successfully!"
    echo "=========================================================================="
    echo ""
    echo "📊 QUICK STATS:"
    echo ""

    # Extract some quick stats from validation report if jq is available
    if command -v jq &> /dev/null; then
        if [ -f "$DIR/validation_report.json" ]; then
            echo "Vault Performance:"
            jq -r '.vault_performance | "  Total Trades: \(.total_trades)\n  Win Rate: \(.win_rate)%\n  Total PnL: $\(.total_pnl)\n  Profit Factor: \(.profit_factor)"' "$DIR/validation_report.json" 2>/dev/null || echo "  (Unable to parse)"
        fi
    else
        echo "  Install 'jq' for detailed stats: brew install jq"
    fi

    echo ""
    echo "📖 NEXT STEPS:"
    echo ""
    echo "1. Review strategy summary:"
    echo "   cat $DIR/strategy_summary.txt"
    echo ""
    echo "2. Check extracted rules:"
    echo "   cat $DIR/extracted_rules.json | jq ."
    echo ""
    echo "3. Follow implementation guide:"
    echo "   cat PASO_A_PASO_VAULT_ANALYSIS.md"
    echo ""
else
    echo "=========================================================================="
    echo "⚠️  SOME FILES MISSING - Analysis may be incomplete"
    echo "=========================================================================="
    echo ""
    echo "Try re-running the analysis:"
    echo "  ./quick_start.sh <vault_address> <symbol> <timeframe>"
fi

echo ""
echo "=========================================================================="
