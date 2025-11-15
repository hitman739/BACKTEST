# Hyperliquid CopyTrade - Quick Start (3 minutos)

Get up and running in 3 minutes on your Mac!

## Prerequisites

```bash
# Check you have Python 3.9+
python3 --version

# Check you have Node.js 18+
node --version
```

## ⚡ SUPER RÁPIDO (3 comandos)

```bash
# 1. Ir a la carpeta
cd hyperliquid-copytrade

# 2. Instalar todo (backend + frontend)
./setup.sh

# 3a. Terminal 1 - Iniciar backend
./start-backend.sh

# 3b. Terminal 2 - Iniciar frontend
./start-frontend.sh
```

Abre `http://localhost:5173` y listo! 🚀

---

## Método Manual (alternativa)

### Step 1: Install (2 minutes)

```bash
# Navigate to project
cd hyperliquid-copytrade

# Install backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend
cd frontend
npm install
cd ..
```

### Step 2: Start Servers (1 minute)

**Terminal 1 - Backend**
```bash
cd backend
source venv/bin/activate
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

## Step 3: Get API Credentials (1 minute)

1. Go to [Hyperliquid Testnet](https://app.hyperliquid.xyz/testnet)
2. Connect your wallet
3. Settings → API → Create API Key
4. **Important**: Only enable "Trading" permissions (NOT withdrawal)
5. Copy your private key (starts with 0x...)

## Step 4: Start Copy Trading (1 minute)

1. Open `http://localhost:5173` in your browser

2. Fill in the form:
   - **API Key**: Your Hyperliquid API key
   - **API Secret**: Your private key (0x...)
   - **Target Wallet**: Trader's address you want to copy (0x...)
   - **Network**: Select **Testnet** (recommended for first run)

3. Click **"Start Copy Trading"**

4. You're live! The dashboard will show:
   - ✅ Connection status
   - ✅ Target wallet being monitored
   - ✅ Real-time trade feed

## Finding a Trader to Copy

**Option 1: Hyperliquid Leaderboard**
1. Go to [Hyperliquid Stats](https://app.hyperliquid.xyz/leaderboard)
2. Browse top traders
3. Copy their wallet address

**Option 2: Known Successful Trader**
- Ask in Hyperliquid Discord/Telegram
- Use a wallet you've been tracking
- Check Hyperliquid Twitter for alpha

## Test It Works

### Create a test trade on testnet:
1. Go to [Hyperliquid Testnet](https://app.hyperliquid.xyz/testnet)
2. Login to the TARGET trader account
3. Open a small position (e.g., 0.01 BTC)
4. Watch your copytrade dashboard
5. Within 5 seconds you should see the trade copied!

## Quick Commands Reference

### Start Everything
```bash
# Terminal 1
cd backend && source venv/bin/activate && python main.py

# Terminal 2 (new terminal)
cd frontend && npm run dev
```

### Stop Everything
- Press `Ctrl+C` in both terminals
- Or click "Stop Copy Trading" in the web interface

### Check Status
```bash
# Test backend is running
curl http://localhost:8000/health

# Should return: {"status":"healthy","copy_active":false}
```

## Common Issues

### Port already in use
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

### Backend won't start
```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Safety Checklist

Before going to mainnet:

- [ ] Tested on testnet successfully
- [ ] Understand margin % copying mechanism
- [ ] API key has NO withdrawal permissions
- [ ] Using small account size initially
- [ ] Monitoring dashboard actively
- [ ] Know how to stop immediately (Stop button)

## What Happens Next?

The bot will:
1. Check target wallet every 5 seconds
2. Detect when they open/close/modify positions
3. Calculate what % of their margin they used
4. Execute the same trade with the same % of YOUR margin
5. Show all activity in real-time on the dashboard

## Example Flow

```
1. Target trader opens position
   → Bot detects in ~5 seconds

2. Bot calculates: "They used 20% of their margin"
   → Bot will use 20% of YOUR margin

3. Bot executes trade on your account
   → You see it in the dashboard immediately

4. Trade appears in your Hyperliquid account
   → Same direction, proportional size
```

## Next Steps

- Read full [README.md](./README.md) for details
- Understand the [margin % formula](./README.md#how-it-works)
- Monitor trades actively
- Start with testnet, move to mainnet when comfortable

## Support

Something wrong?
1. Check both terminal outputs for errors
2. Check browser console (F12 → Console tab)
3. Verify API credentials are correct
4. Ensure target wallet is actually trading

---

**Ready to trade? Let's go! 🚀**

Remember: Always start on testnet first!
