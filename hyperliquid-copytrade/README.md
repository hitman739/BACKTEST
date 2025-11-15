# Hyperliquid CopyTrade

Private copy trading system for Hyperliquid that copies trades based on margin percentage used, not nominal size.

## Key Innovation

Instead of copying the exact trade size, this bot copies the **percentage of margin** used by the trader. This makes it scalable regardless of account size differences.

**Example:**
- Trader has $10,000 and opens a position using $1,000 margin (10%)
- You have $1,000 and the bot will use $100 margin (10%)
- Proportional copying that works with any account size!

## Features

- ✅ Copy trades based on margin % (not nominal size)
- ✅ Real-time trade monitoring via WebSocket
- ✅ Simple web interface
- ✅ Testnet support for safe testing
- ✅ Automatic position sizing
- ✅ Live trade feed

## Stack

- **Backend**: Python + FastAPI + hyperliquid-python-sdk
- **Frontend**: React + Vite + TailwindCSS
- **Real-time**: WebSocket for instant updates

## Prerequisites

- Python 3.9+
- Node.js 18+
- Hyperliquid account with API credentials
- Mac (tested on macOS)

## Quick Start (4 comandos)

```bash
# 1. Clonar o pull del repo
git pull origin claude/hola-01MHMV9SsYEYGhoohLKGaXA8

# 2. Navegar a la carpeta
cd hyperliquid-copytrade

# 3. Instalar todo (backend + frontend)
./setup.sh

# 4a. En Terminal 1 - Ejecutar backend
./start-backend.sh

# 4b. En Terminal 2 - Ejecutar frontend
./start-frontend.sh
```

Abre el navegador en: `http://localhost:5173`

---

## Installation Manual (alternativa)

Si prefieres instalar manualmente:

### 1. Clone the repository

```bash
cd hyperliquid-copytrade
```

### 2. Install Backend Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## Configuration

### Get Hyperliquid API Credentials

1. Go to [Hyperliquid](https://app.hyperliquid.xyz/)
2. Connect your wallet
3. Go to Settings → API
4. Create new API key with **Trading permissions only** (NO withdraw permissions for safety)
5. Save your private key securely

### Find Target Wallet

1. Find a successful trader on Hyperliquid
2. Copy their wallet address (0x...)
3. You'll paste this in the web interface

## Usage

### Step 1: Start Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

Backend will run on `http://localhost:8000`

### Step 2: Start Frontend

Open a new terminal:

```bash
cd frontend
npm run dev
```

Frontend will run on `http://localhost:5173`

### Step 3: Open Web Interface

Open your browser to `http://localhost:5173`

### Step 4: Start Copy Trading

1. **Enter your API Key** (from Hyperliquid)
2. **Enter your API Secret** (your private key starting with 0x...)
3. **Paste target wallet address** (the trader you want to copy)
4. **Choose network**:
   - Start with **Testnet** to verify everything works
   - Switch to **Mainnet** when ready
5. **Click "Start Copy Trading"**

The bot will now:
- Monitor the target wallet every 5 seconds
- Detect new positions, size changes, and closes
- Calculate margin % used by the trader
- Execute the same trade with the same margin % in your account
- Show all trades in real-time on the dashboard

## How It Works

### Margin % Calculation

```
Trader's margin % = (margin_used / account_value) * 100

Your position size = (your_account_value * margin% / 100 * leverage) / price
```

### Example Scenario

**Target Trader:**
- Account value: $50,000
- Opens BTC long position
- Position size: 2 BTC @ $40,000 = $80,000
- Leverage: 5x
- Margin used: $16,000
- Margin %: 32%

**Your Account:**
- Account value: $5,000
- Bot calculates: 32% margin = $1,600
- With 5x leverage: Position value = $8,000
- Position size: 0.2 BTC @ $40,000
- **You just copied the trade proportionally!**

## Safety Features

- **API key permissions**: Only trading, no withdrawals
- **Testnet mode**: Test everything safely first
- **Real-time monitoring**: See every trade before execution
- **Stop button**: Instantly stop copying at any time

## API Endpoints

Backend exposes these endpoints:

- `GET /` - Health check
- `POST /start-copy` - Start copy trading
- `POST /stop-copy` - Stop copy trading
- `GET /status` - Get current status
- `WebSocket /ws` - Real-time updates

## Troubleshooting

### Backend won't start
```bash
# Make sure virtual environment is activated
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### No trades copying
- Verify target wallet is actually trading
- Check network (testnet vs mainnet)
- Ensure API key has correct permissions
- Check backend logs for errors

### WebSocket disconnected
- Backend must be running on port 8000
- Frontend must be running on port 5173
- Check firewall settings

## Development

### Run backend in development mode with auto-reload
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Run frontend in development mode
```bash
cd frontend
npm run dev
```

## Architecture

```
┌─────────────────────┐
│   Web Interface     │  React + TailwindCSS
│   (localhost:5173)  │
└──────────┬──────────┘
           │ WebSocket + HTTP
           │
┌──────────▼──────────┐
│   FastAPI Server    │  Python Backend
│   (localhost:8000)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  CopyTradeManager   │  Core Logic
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Hyperliquid SDK     │  API Integration
└─────────────────────┘
```

## License

Private use only. Not for redistribution.

## Warning

**Use at your own risk.** Always:
- Start with testnet
- Use small amounts
- Never share your private key
- Monitor trades actively
- Understand the risks of leverage

## Support

For issues, check the logs:
- Backend: Terminal running `python main.py`
- Frontend: Browser console (F12)
- Network: Browser Network tab (F12)

---

Built with ❤️ for automated crypto trading
