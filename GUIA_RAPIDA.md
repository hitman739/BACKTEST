# 🚀 GUÍA RÁPIDA - Analizar Traders de Hyperliquid

## ⚡ Método Simple (SIN complicaciones)

### PASO 1: Descargar datos de TradingView (2 minutos)

1. **Abre TradingView:**
   ```
   https://www.tradingview.com/chart/
   ```

2. **Busca el símbolo:**
   - Para HYPE: escribe `HYPERLIQUID:HYPE`
   - Para BTC: escribe `BINANCE:BTCUSDT`
   - Para SOL: escribe `BINANCE:SOLUSDT`

3. **Configura:**
   - Timeframe: Selecciona `5m` (arriba a la izquierda)
   - Zoom: Arrastra para ver últimos 30 días

4. **Exporta:**
   - Click derecho en el chart
   - "Export chart data..."
   - Guarda como: `HYPE_5m.csv` (en tu carpeta BACKTEST)

---

### PASO 2: Cargar datos (10 segundos)

```bash
cd ~/Documents/BACKTEST

# Cargar el CSV descargado
python3 load_tradingview_simple.py HYPE_5m.csv 0xTRADER_ADDRESS
```

**Output:**
```
✅ Processed successfully
   Candles: 8640
   From: 2024-10-14
   To: 2024-11-13
💾 Saved to: reports/reverse_engineering/0x.../ohlcv_tradingview.parquet
```

---

### PASO 3: Analizar trader (1-2 minutos)

```bash
python3 reanalyze_with_indicators.py
```

**Output:**
```
✅ Generated 100+ features
🎯 SCORE: 8/12
📈 ENTRY RULES:
  SHORT:
    - EMA20 < EMA50
    - Price < EMA20
    - RSI > 70
    ...
```

---

### PASO 4: Ver estrategia

```bash
cat reports/reverse_engineering/0x.../strategy_summary_with_indicators.txt
```

**¡LISTO! Estrategia extraída con datos PRECISOS.** ✅

---

## 🎯 Workflow Completo (desde cero)

```bash
# 1. Encuentra trader
https://app.hyperliquid.xyz/leaderboard
# Copia dirección: 0x8bae3527...

# 2. Test rápido
./test.sh 0x8bae3527...
# Output: Symbol: HYPE, Score: 8/12 ✅

# 3. Descarga datos de TradingView
# → https://www.tradingview.com/chart/
# → Busca HYPERLIQUID:HYPE
# → Exporta como HYPE_5m.csv

# 4. Analiza trader completo
python3 reverse_engineer_vault_complete.py \
  --vault 0x8bae3527... \
  --symbol HYPE \
  --timeframe 5m

# 5. Carga datos precisos de TradingView
python3 load_tradingview_simple.py HYPE_5m.csv 0x8bae3527...

# 6. Re-analiza con datos REALES
python3 reanalyze_with_indicators.py

# 7. Ver estrategia
cat reports/reverse_engineering/0x8bae3527/strategy_summary_with_indicators.txt
```

---

## 📋 Checklist

- [ ] Encontrar trader en leaderboard
- [ ] Test: `./test.sh 0xADDRESS`
- [ ] Score ≥ 7 → Continuar
- [ ] Ir a TradingView web
- [ ] Buscar símbolo del trader
- [ ] Exportar CSV (últimos 30 días, timeframe 5m)
- [ ] Cargar CSV: `python3 load_tradingview_simple.py SYMBOL.csv 0xADDRESS`
- [ ] Analizar: `python3 reverse_engineer_vault_complete.py --vault 0xADDRESS --symbol SYMBOL`
- [ ] Re-analizar con datos reales: `python3 reanalyze_with_indicators.py`
- [ ] Ver estrategia: `cat reports/.../strategy_summary_with_indicators.txt`

---

## 💡 Tips

✅ **Usa 5m para scalping/day trading**
✅ **Usa 15m o 1h para swing trading**
✅ **Descarga mínimo 30 días de datos**
✅ **Verifica que el CSV tenga columnas: time, open, high, low, close, volume**

---

## 🐛 Problemas Comunes

**"File not found"**
→ Verifica que el CSV esté en la carpeta BACKTEST

**"Missing columns"**
→ Asegúrate de exportar desde TradingView, no de otra fuente

**"No data"**
→ El símbolo puede no estar disponible, prueba otro exchange en TradingView

---

¡Ahora puedes analizar CUALQUIER trader con datos 100% precisos! 🎯
