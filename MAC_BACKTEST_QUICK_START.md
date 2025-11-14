# ⚡ Quick Start - Backtest en Mac

## 🎯 Objetivo

Correr backtest de **TETR strategy** en:
- **BTCUSDT** (Bitcoin)
- **ETHUSDT** (Ethereum)
- **SOLUSDT** (Solana)

Con datos reales de Binance, últimos 60 días, timeframe **15m**.

---

## 🚀 Opción 1: Un Solo Comando (RECOMENDADO)

```bash
cd ~/BACKTEST  # o donde esté tu repo
./run_mac_backtest.sh
```

**¡Listo!** El script hace todo automáticamente:
1. ✅ Descarga datos de Binance
2. ✅ Corre backtest en 3 pares
3. ✅ Muestra resultados comparativos

**Tiempo estimado:** 2-3 minutos

---

## 📊 Opción 2: Paso a Paso

### Paso 1: Descargar Datos
```bash
python3 prepare_data.py
```

**Output esperado:**
```
✅ Successfully downloaded:
   BTCUSDT: 5760 candles (Sep 15 - Nov 14)
   ETHUSDT: 5760 candles
   SOLUSDT: 5760 candles
```

### Paso 2: Ejecutar Backtest
```bash
python3 backtest_multi_pairs.py
```

**Output esperado:**
```
📊 MULTI-PAIR COMPARISON

Pair     Return %  Trades  Win Rate  Profit Factor  Final $
BTCUSDT    +2.45%      28     42.9%           1.35  $10,245
ETHUSDT    +1.83%      24     37.5%           1.21  $10,183
SOLUSDT    +3.12%      32     40.6%           1.42  $10,312

🏆 Best Performer: SOLUSDT
   Return: +3.12%
   Sharpe: 0.18
```

---

## 📁 Archivos que Recibirás

```
BACKTEST/
├── data/binance/              # Datos descargados
│   ├── BTCUSDT/15m.parquet   # ~1-2 MB cada uno
│   ├── ETHUSDT/15m.parquet
│   └── SOLUSDT/15m.parquet
│
└── reports/                   # Resultados del backtest
    ├── tetr_BTCUSDT_15m_20241114_*/
    │   ├── summary.json       # Métricas generales
    │   ├── trades.csv         # Lista de todos los trades
    │   └── equity_curve.csv   # Evolución del capital
    ├── tetr_ETHUSDT_15m_*/
    └── tetr_SOLUSDT_15m_*/
```

---

## 🔧 Configuración

Todos los parámetros están en `backtest_multi_pairs.py`:

```python
PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']  # Línea 14
TIMEFRAME = '15m'                           # Línea 15
DAYS_BACK = 60                              # Línea 16
INITIAL_BALANCE = 10000                     # Línea 17
```

**Para cambiar pares:**
```python
# Ejemplos:
PAIRS = ['BTCUSDT', 'BNBUSDT', 'ADAUSDT']
PAIRS = ['BTCUSDT', 'LINKUSDT', 'DOTUSDT']
```

**Para cambiar timeframe:**
```python
TIMEFRAME = '5m'   # Más trades, más ruido
TIMEFRAME = '15m'  # Balance (RECOMENDADO)
TIMEFRAME = '1h'   # Menos trades, señales más limpias
```

**Para cambiar período:**
```python
DAYS_BACK = 30   # Último mes
DAYS_BACK = 60   # Últimos 2 meses (DEFAULT)
DAYS_BACK = 90   # Últimos 3 meses
```

---

## ⚠️ Troubleshooting

### "Cannot connect to Binance"

**Solución 1: Usar VPN**
- Binance puede estar bloqueado en tu región
- Conecta VPN y vuelve a ejecutar

**Solución 2: Verificar cache**
```bash
ls -lh data/binance/*/15m.parquet
# Si ves archivos, los datos ya existen
# Ejecuta solo: python3 backtest_multi_pairs.py
```

### "Module not found"

```bash
pip3 install pandas numpy aiohttp ccxt
```

### "Permission denied"

```bash
chmod +x run_mac_backtest.sh
chmod +x prepare_data.py
chmod +x backtest_multi_pairs.py
```

---

## 📊 Interpretar Resultados

### Buenas Métricas
```
✅ Return: >2%
✅ Win Rate: >35%
✅ Profit Factor: >1.2
✅ Sharpe: >0.1
✅ Max Drawdown: <10%
```

### Métricas Malas
```
❌ Return: <0%
❌ Win Rate: <30%
❌ Profit Factor: <1.0
❌ Sharpe: <0
❌ Max Drawdown: >15%
```

### Ejemplo Real (Bueno)
```
SOLUSDT:
  Return: +3.12%      ✅ Profitable
  Win Rate: 40.6%     ✅ Decent
  Profit Factor: 1.42 ✅ Good
  Sharpe: 0.18        ✅ Positive
  Max DD: 9.1%        ✅ Acceptable

Veredicto: ✅ Strategy funciona bien en SOL
```

### Ejemplo Real (Malo)
```
BTCUSDT:
  Return: -1.5%       ❌ Losing
  Win Rate: 28.0%     ❌ Low
  Profit Factor: 0.85 ❌ <1.0
  Sharpe: -0.05       ❌ Negative
  Max DD: 12.3%       ❌ High

Veredicto: ❌ Strategy no funciona en este período
```

---

## 🎯 Qué Hacer Después

### Si los resultados son BUENOS (Return >2%, PF >1.2)

1. **Validar en otro período:**
   ```python
   DAYS_BACK = 90  # Testear 3 meses
   ```

2. **Optimizar parámetros:**
   - Edita `strategies/tetr_strategy.py`
   - Prueba diferentes EMAs (8/21/55)
   - Ajusta pullback_tolerance

3. **Paper trading:**
   - Si consistente en 60-90 días
   - Prueba en tiempo real (sin riesgo)

### Si los resultados son MALOS (Return <0%, PF <1.0)

1. **Probar otro timeframe:**
   ```python
   TIMEFRAME = '1h'  # Menos ruido
   ```

2. **Agregar filtros:**
   - ADX > 25 (solo trends fuertes)
   - Volatility filter
   - Volume confirmation

3. **Probar otro período:**
   - Puede ser que el mercado estaba lateral
   - Cambia fechas y retesta

---

## 📈 Comandos Útiles

**Ver datos descargados:**
```bash
python3 -c "
import pandas as pd
df = pd.read_parquet('data/binance/BTCUSDT/15m.parquet')
print(f'Candles: {len(df)}')
print(f'From: {df.iloc[0][\"timestamp\"]}')
print(f'To: {df.iloc[-1][\"timestamp\"]}')
"
```

**Ver mejores trades:**
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('reports/tetr_BTCUSDT_15m_*/trades.csv')
print(df.nlargest(5, 'pnl')[['entry_time', 'pnl', 'exit_reason']])
"
```

**Limpiar datos y redescargar:**
```bash
rm -rf data/binance/*
python3 prepare_data.py
```

---

## ❓ FAQ

**Q: ¿Cuánto tarda todo el proceso?**
A: ~2-3 minutos total (descarga + backtest)

**Q: ¿Necesito API key de Binance?**
A: No, los datos son públicos

**Q: ¿Puedo testear en más pares?**
A: Sí, agrega más símbolos al array `PAIRS`

**Q: ¿Por qué 15m y no 5m?**
A: 15m tiene menos ruido, señales más confiables

**Q: ¿Los datos se guardan?**
A: Sí, en `data/binance/`. Próxima vez es más rápido

**Q: ¿Puedo cambiar la estrategia?**
A: Sí, cambia `TETRStrategy()` por otra estrategia

---

## 📞 Si Necesitas Ayuda

1. Revisa `RUN_ON_MAC.md` (guía detallada)
2. Revisa logs de error en la terminal
3. Verifica que Python 3.9+ esté instalado
4. Asegúrate que Binance API sea accesible

---

**Creado:** 14 Nov 2024
**Para:** Mac OS
**Python:** 3.9+
**Estrategia:** TETR (Triple EMA Trend Rider)
**Timeframe:** 15m (recomendado)
