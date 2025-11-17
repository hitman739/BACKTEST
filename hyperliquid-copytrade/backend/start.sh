#!/bin/bash

# =============================================================================
# Hyperliquid Copy Trading - Unified Backend Startup Script
# =============================================================================
# This script starts the unified backend with both Simulator and Ultra modules
#
# Usage:
#   ./start.sh [--port PORT] [--reload]
#
# Options:
#   --port PORT    Port to run the server on (default: 8000)
#   --reload       Enable auto-reload on code changes (development mode)
#
# =============================================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
PORT=8000
RELOAD=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --reload)
            RELOAD="--reload"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}🚀 Starting Hyperliquid Copy Trading - Unified Backend${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Configuration:${NC}"
echo -e "   Port: ${GREEN}${PORT}${NC}"
echo -e "   Reload: ${GREEN}${RELOAD:-disabled}${NC}"
echo -e "   Modules: ${GREEN}Simulator + Ultra Copy Trading${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file. Please review and update if needed.${NC}"
    echo ""
fi

# Start the server
echo -e "${BLUE}=============================================================================${NC}"
echo -e "${GREEN}🌐 Starting server on http://0.0.0.0:${PORT}${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""
echo -e "${YELLOW}📖 API Documentation:${NC} http://localhost:${PORT}/docs"
echo -e "${YELLOW}💚 Health Check:${NC} http://localhost:${PORT}/health"
echo ""
echo -e "${BLUE}Available endpoints:${NC}"
echo -e "   • ${GREEN}/api/auth${NC} - Authentication"
echo -e "   • ${GREEN}/api/account${NC} - Account management"
echo -e "   • ${GREEN}/api/simulator${NC} - Copy trading simulator"
echo -e "   • ${GREEN}/api/ultra${NC} - Ultra copy trading (REAL)"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo -e "${BLUE}=============================================================================${NC}"
echo ""

# Start uvicorn
python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT} ${RELOAD}
