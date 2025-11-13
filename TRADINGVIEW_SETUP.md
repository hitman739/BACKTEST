# 📊 Usar TradingView para Datos Precisos

## ✅ VENTAJAS

TradingView tiene datos **REALES** de:
- ✅ Hyperliquid (HYPE, PURR, etc.)
- ✅ Binance (BTC, ETH, SOL)
- ✅ Bybit, OKX, Coinbase
- ✅ Todos los timeframes (1m, 5m, 15m, 1h, 4h, 1d)

**Soluciona el problema de APIs bloqueadas (403)**

---

## 🚀 Setup (una sola vez)

```bash
# Instalar biblioteca
pip3 install tvdatafeed

# O si tienes problemas:
pip install tvdatafeed
```

---

## 📥 Descargar Datos

### Método 1: Script automático

```bash
# Descargar HYPE, últimos 30 días, timeframe 5m
python3 load_tradingview_data.py HYPE 5m 30

# Descargar BTC, últimos 60 días, timeframe 15m
python3 load_tradingview_data.py BTC 15m 60

# Descargar SOL, últimos 90 días, timeframe 1h
python3 load_tradingview_data.py SOL 1h 90
```

**Output:**
```
✅ Data loaded successfully
   Bars: 8640
   From: 2024-10-14
   To: 2024-11-13

💾 Saved to: data/tradingview/HYPE/ohlcv.parquet
💾 Also saved as CSV: data/tradingview/HYPE/ohlcv.csv
```

---

### Método 2: Manual desde TradingView Web

Si el script falla:

1. **Ve a TradingView:**
   ```
   https://www.tradingview.com/chart/
   ```

2. **Selecciona símbolo:**
   - HYPERLIQUID:HYPE
   - BINANCE:BTCUSDT
   - etc.

3. **Exporta datos:**
   - Click derecho en chart → "Export chart data"
   - Descarga CSV
   - Guarda como `hyperliquid_hype_5m.csv`

4. **Carga el CSV:**
   ```bash
   python3 load_manual_ohlcv.py hyperliquid_hype_5m.csv 0xTRADER_ADDRESS
   ```

---

## 🔬 Usar con Análisis de Vault

### Workflow Completo:

```bash
# 1. Encuentra trader
./test.sh 0xTRADER_ADDRESS
# Output: Symbol: HYPE, Score: 8/12 ✅

# 2. Descarga datos REALES de HYPE desde TradingView
python3 load_tradingview_data.py HYPE 5m 30

# 3. Analiza trader con datos REALES
python3 reverse_engineer_vault_complete.py \
  --vault 0xTRADER_ADDRESS \
  --symbol HYPE \
  --timeframe 5m \
  --data-source tradingview

# 4. Ver estrategia
cat reports/reverse_engineering/0x.../strategy_summary.txt
```

---

## 🎯 Ventajas vs Otras Opciones

| Método | Pros | Contras |
|--------|------|---------|
| **TradingView** ✅ | Datos precisos, Todos los símbolos, No requiere API key | Requiere pip install |
| Binance API | Oficial, Rápido | Solo símbolos en Binance |
| Hyperliquid API | Datos nativos | Bloqueado (403) |
| Reconstruir desde trades | Automático | ❌ IMPRECISO |

---

## 📋 Timeframes Disponibles

- `1m` - 1 minuto
- `5m` - 5 minutos (recomendado para scalping)
- `15m` - 15 minutos (recomendado para day trading)
- `30m` - 30 minutos
- `1h` - 1 hora (recomendado para swing)
- `2h` - 2 horas
- `4h` - 4 horas
- `1d` - 1 día

---

## 🐛 Troubleshooting

### Error: "tvdatafeed not installed"

```bash
pip3 install tvdatafeed
```

### Error: "Could not fetch data"

Intenta con otro exchange:
- HYPERLIQUID:HYPE
- BINANCE:BTCUSDT
- BYBIT:BTCUSDT

O descarga manualmente desde web.

### Error: Rate limit

TradingView puede limitar requests. Espera 1 minuto y reintenta.

---

## ✅ Workflow Recomendado

```bash
# 1. Busca trader en leaderboard
https://app.hyperliquid.xyz/leaderboard

# 2. Test trader
./test.sh 0xTRADER_ADDRESS

# 3. Descarga OHLCV desde TradingView (datos REALES)
python3 load_tradingview_data.py SYMBOL 5m 30

# 4. Analiza con datos precisos
python3 reverse_engineer_vault_complete.py \
  --vault 0xTRADER_ADDRESS \
  --symbol SYMBOL \
  --timeframe 5m

# 5. ✅ Estrategia con indicadores PRECISOS
cat reports/reverse_engineering/0x.../strategy_summary.txt
```

---

**¡Ahora puedes analizar CUALQUIER símbolo con datos 100% precisos!** 🎯
