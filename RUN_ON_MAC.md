# 🚀 Ejecutar Backtest en Mac - Guía Rápida

## 📋 Prerequisitos

```bash
# Verificar Python (necesitas 3.9+)
python3 --version

# Verificar dependencias
pip3 list | grep -E "pandas|numpy|aiohttp|ccxt"
```

Si falta alguna dependencia:
```bash
pip3 install pandas numpy aiohttp ccxt
```

---

## ⚡ Opción 1: Script Todo-en-Uno (RECOMENDADO)

Este script descarga datos + corre backtest automáticamente:

```bash
cd ~/BACKTEST  # o donde tengas el repo
chmod +x run_mac_backtest.sh
./run_mac_backtest.sh
```

**Hecho!** El script hace todo automáticamente.

---

## 📊 Opción 2: Paso a Paso (Control Manual)

### Paso 1: Descargar Datos

```bash
python3 prepare_data.py
```

Esto descarga datos de Binance para:
- **BTCUSDT** (Bitcoin)
- **ETHUSDT** (Ethereum)
- **SOLUSDT** (Solana)

Timeframe: **15m**
Período: **Últimos 60 días**

**Output esperado:**
```
✅ Successfully downloaded:
   BTCUSDT: 5760 candles
   ETHUSDT: 5760 candles
   SOLUSDT: 5760 candles
```

### Paso 2: Ejecutar Backtest

```bash
python3 backtest_multi_pairs.py
```

Esto corre **TETR strategy** en los 3 pares.

**Output esperado:**
```
📊 MULTI-PAIR COMPARISON

Pair     Return %  Trades Win Rate Profit Factor Sharpe Max DD Avg R   Final $
BTCUSDT    +2.45%      28    42.9%          1.35   0.15   8.5% 0.24  $10245.00
ETHUSDT    +1.83%      24    37.5%          1.21   0.12   7.2% 0.18  $10183.00
SOLUSDT    +3.12%      32    40.6%          1.42   0.18   9.1% 0.28  $10312.00

🏆 Best Performer: SOLUSDT
```

---

## 🔧 Troubleshooting

### Error: "Cannot connect to Binance"

**Opción A: Usar VPN**
```bash
# Si Binance está bloqueado en tu país
# 1. Conecta VPN
# 2. Ejecuta de nuevo prepare_data.py
```

**Opción B: Usar datos cacheados**
```bash
# Si ya descargaste datos antes:
python3 backtest_multi_pairs.py
# El script usa cache automáticamente
```

**Opción C: Descargar manualmente**
```bash
# Ve a data/binance/ y verifica si hay archivos .parquet
ls -lh data/binance/*/15m.parquet
```

### Error: "ModuleNotFoundError"

```bash
# Instalar dependencias faltantes
pip3 install -r requirements.txt

# O manualmente:
pip3 install pandas numpy aiohttp ccxt
```

### Error: "Permission denied"

```bash
# Dar permisos de ejecución
chmod +x prepare_data.py
chmod +x backtest_multi_pairs.py
chmod +x run_mac_backtest.sh
```

---

## 📁 Archivos Generados

Después de ejecutar, encontrarás:

```
BACKTEST/
├── data/binance/           # Datos descargados
│   ├── BTCUSDT/15m.parquet
│   ├── ETHUSDT/15m.parquet
│   └── SOLUSDT/15m.parquet
│
└── reports/                # Resultados
    ├── tetr_BTCUSDT_15m_*/
    ├── tetr_ETHUSDT_15m_*/
    └── tetr_SOLUSDT_15m_*/
```

Cada carpeta de reports contiene:
- `summary.json` - Métricas del backtest
- `trades.csv` - Todos los trades
- `equity_curve.csv` - Curva de equity

---

## 📊 Qué Esperar

### TETR en 15m (últimos 60 días)

**Performance típica:**
```
Return:       1-5% (dependiendo del mercado)
Trades:       20-40 por par
Win Rate:     35-45%
Profit Factor: 1.2-1.5
Max Drawdown: 5-12%
```

**Mejor en:**
- ✅ Mercados con tendencia clara
- ✅ Alta volatilidad
- ✅ Pares líquidos (BTC, ETH, SOL)

**Peor en:**
- ❌ Mercados laterales
- ❌ Baja volatilidad
- ❌ Pares con bajo volumen

---

## 🎯 Comandos Rápidos

```bash
# Solo descargar datos (no backtest)
python3 prepare_data.py

# Solo backtest (asume datos ya descargados)
python3 backtest_multi_pairs.py

# Ver datos descargados
python3 -c "
import pandas as pd
df = pd.read_parquet('data/binance/BTCUSDT/15m.parquet')
print(f'Candles: {len(df)}')
print(f'From: {df[\"timestamp\"].min()}')
print(f'To: {df[\"timestamp\"].max()}')
"

# Analizar trades de un par específico
python3 -c "
import pandas as pd
trades = pd.read_csv('reports/tetr_BTCUSDT_15m_*/trades.csv')
print(trades[['entry_time', 'pnl', 'exit_reason']].head(10))
"
```

---

## 🔄 Cambiar Configuración

### Cambiar Pares

Edita `backtest_multi_pairs.py` línea 14:
```python
PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
# Cambia a:
PAIRS = ['BTCUSDT', 'BNBUSDT', 'ADAUSDT']
```

### Cambiar Timeframe

Edita línea 15:
```python
TIMEFRAME = '15m'
# Cambia a:
TIMEFRAME = '1h'  # o '5m', '30m', '4h'
```

### Cambiar Período

Edita línea 16:
```python
DAYS_BACK = 60
# Cambia a:
DAYS_BACK = 90  # últimos 3 meses
```

---

## 📈 Optimización (Opcional)

Si quieres optimizar TETR para mejores resultados:

```bash
# Agregar filtro ADX (solo trends fuertes)
# Edita strategies/tetr_strategy.py y agrega:
# if ADX < 25: return False

# Cambiar EMAs (probar Fibonacci)
# En tetr_strategy.py línea 28-30:
'ema_fast': 8,   # en vez de 9
'ema_mid': 21,   # mantener
'ema_slow': 55,  # mantener

# Ajustar tolerancia de pullback
'pullback_tolerance': 0.005,  # en vez de 0.003 (más permisivo)
```

---

## ❓ FAQ

**Q: ¿Cuánto tarda en descargar los datos?**
A: ~30 segundos por par (total ~2 minutos para 3 pares)

**Q: ¿Cuánto tarda el backtest?**
A: ~10-20 segundos por par (total ~1 minuto)

**Q: ¿Puedo testear más de 3 pares?**
A: Sí, solo agrega a la lista `PAIRS` en el script

**Q: ¿Los datos se guardan?**
A: Sí, en `data/binance/`. La próxima vez usa cache (más rápido)

**Q: ¿Puedo testear otras estrategias?**
A: Sí, cambia `TETRStrategy()` por:
- `VCBStrategy()` - Volatility Compression
- `MREStrategy()` - Mean Reversion
- `VSMStrategy()` - Volume Spike
- `SRBStrategy()` - Support/Resistance

**Q: ¿Cómo veo los resultados detallados?**
A: Revisa `reports/tetr_SYMBOL_15m_*/trades.csv` en Excel

---

## 🎯 Next Steps

Después de correr el backtest:

1. **Analiza resultados:**
   - ¿Qué par funcionó mejor?
   - ¿Win rate aceptable (>35%)?
   - ¿Profit factor >1.2?

2. **Optimiza parámetros:**
   - Ajusta EMAs
   - Cambia tolerancias
   - Agrega filtros (ADX, volumen)

3. **Valida en otro período:**
   - Cambia `DAYS_BACK = 90`
   - Verifica consistencia

4. **Paper trading:**
   - Si results son buenos (>2% return, PF >1.3)
   - Prueba en tiempo real

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs del script
2. Verifica conexión a internet
3. Comprueba que Binance API sea accesible
4. Usa VPN si Binance está bloqueado

---

**Created:** Nov 14, 2024
**For:** Mac OS
**Python:** 3.9+
**Strategy:** TETR (Triple EMA Trend Rider)
