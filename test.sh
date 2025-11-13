#!/bin/bash
# Quick test script for any Hyperliquid trader/vault

if [ -z "$1" ]; then
    echo "Usage: ./test.sh <wallet_address> [symbol]"
    echo ""
    echo "Examples:"
    echo "  ./test.sh 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d"
    echo "  ./test.sh 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d SOL"
    exit 1
fi

WALLET=$1
SYMBOL=$2

echo "=========================================="
echo "🧪 QUICK TEST"
echo "=========================================="
echo "Wallet: $WALLET"
if [ ! -z "$SYMBOL" ]; then
    echo "Symbol filter: $SYMBOL"
fi
echo ""

python3 find_best_traders.py "$WALLET" $SYMBOL
