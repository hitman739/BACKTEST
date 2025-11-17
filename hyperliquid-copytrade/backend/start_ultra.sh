#!/bin/bash

# Start Ultra-Low Latency Copy Trading System

echo "="
echo "🚀 Ultra-Low Latency Copy Trading System"
echo "="
echo ""
echo "Architecture:"
echo "  ⚡ WebSocket-based (no REST polling)"
echo "  🎯 Target latency: < 100ms (evento → orden)"
echo "  💾 In-memory state (no database overhead)"
echo "  🔥 Non-blocking async execution"
echo "  📊 Real-time latency tracking"
echo ""

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q fastapi uvicorn hyperliquid-python-sdk

echo ""
echo "Starting Ultra Copy Trading API on http://0.0.0.0:8000"
echo "="
echo ""

python api_ultra.py
