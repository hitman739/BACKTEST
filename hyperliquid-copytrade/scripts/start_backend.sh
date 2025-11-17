#!/bin/bash

# =============================================================================
# Quick Start Script for Hyperliquid Copy Trading Backend
# =============================================================================
# This is a convenience wrapper that calls the actual start script
# =============================================================================

cd "$(dirname "$0")/hyperliquid-copytrade/backend" || exit 1
./start.sh "$@"
