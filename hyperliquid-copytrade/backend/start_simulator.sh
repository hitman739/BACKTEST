#!/bin/bash

# Startup script for Hyperliquid Copy Trading Simulator
# Starts the proportional copy trading simulation backend

echo "========================================"
echo "Hyperliquid Copy Trading Simulator v3.0"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "api_simulator.py" ]; then
    echo "❌ Error: api_simulator.py not found"
    echo "Please run this script from the backend directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting simulator backend..."
echo "   API will be available at: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the API
python api_simulator.py
