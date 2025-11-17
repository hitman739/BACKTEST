#!/bin/bash

# Start Hyperliquid CopyTrade API v2
# This version uses WebSocket indexer + local database for fast queries

echo "🚀 Starting Hyperliquid CopyTrade API v2..."
echo ""
echo "Architecture:"
echo "  - WebSocket indexer for real-time Hyperliquid data"
echo "  - Local SQLite database for fast queries"
echo "  - Metrics calculator running every 60 seconds"
echo "  - WebSocket broadcasts to frontend every 1 second"
echo ""

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
pip install -q fastapi uvicorn websockets hyperliquid-python-sdk

# Run the API
echo "Starting API on http://0.0.0.0:8000"
echo ""
python api_new.py
