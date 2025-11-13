# 🚀 QUICK START - Test Traders en 10 segundos

## Paso 1: Setup (una sola vez)

```bash
cd ~/Documents/BACKTEST
git pull origin claude/crypto-backtesting-engine-011CV62u5DmKHc9EuChAZEG5
chmod +x test.sh
```

## Paso 2: Testea cualquier wallet

```bash
# Formato simple
./test.sh 0xWALLET_ADDRESS

# Con filtro de símbolo
./test.sh 0xWALLET_ADDRESS SOL
```

---

## 📊 Ejemplos

```bash
# Test trader
./test.sh 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d

# Test trader - solo trades de SOL
./test.sh 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d SOL
```

---

## 🎯 Qué buscar en el output

### ✅ BUEN trader (Score ≥ 7):
```
✅ Total trades: 150+
💰 Win Rate: 60-85%
💰 Total PnL: $500+
⏱️  Median time between trades: 30+ mins
📈 Symbol: BTC, ETH, SOL, AVAX
🎯 SCORE: 7-12/12
🌟 EXCELLENT - Highly replicable!
```

### ❌ MAL trader (Score < 5):
```
⚠️  Total trades: < 50
⚠️  Win Rate: < 60% or > 90%
⚠️  Time between trades: < 10 mins (HFT)
📈 Symbol: Exotic/illiquid
🎯 SCORE: 0-4/12
❌ POOR - Not recommended
```

---

## 🔄 Si encuentras un BUEN trader

El script te dará el comando exacto:

```bash
python3 reverse_engineer_vault_complete.py \
  --vault 0xTRADER_ADDRESS \
  --symbol SOL \
  --timeframe 5m
```

Copia y ejecuta ese comando.

---

## 📍 Dónde encontrar traders

1. **Leaderboard**: https://app.hyperliquid.xyz/leaderboard
2. **Explorer**: https://app.hyperliquid.xyz/explorer
3. **Twitter**: Busca #Hyperliquid traders
4. **Discord**: Canal de Hyperliquid

---

## ⚡ Workflow completo

```bash
# 1. Encuentra wallet en Hyperliquid
# 2. Test rápido
./test.sh 0xWALLET

# 3. Si score ≥ 7, analiza completo
python3 reverse_engineer_vault_complete.py --vault 0xWALLET --symbol SOL --timeframe 5m

# 4. Si símbolo NO está en Binance
python3 reconstruct_ohlcv_from_trades.py
python3 reanalyze_with_indicators.py

# 5. Ver estrategia
cat reports/reverse_engineering/0x.../strategy_summary_with_indicators.txt
```

---

## 💡 Tips

- Testea 5-10 traders hasta encontrar uno bueno
- Prefiere: BTC, ETH, SOL, AVAX
- Evita: Win rate > 90%, holding time < 10 mins
- Score ideal: 8-12/12

---

¡Listo para encontrar estrategias ganadoras! 🎯
