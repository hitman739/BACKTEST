# 🆚 Comparar TETR Original vs TETR Ultra

## 🎯 Qué Hace Este Test

Corre **ambas versiones** de TETR en los mismos 3 pares (BTC/ETH/SOL) para ver si las optimizaciones mejoran el rendimiento.

Tu backtest anterior mostró:
- **Average: -0.76%** ❌
- Solo ETHUSDT profitable (+1.02%)
- BTCUSDT y SOLUSDT con pérdidas

TETR Ultra debería mejorar esto con:
- ✅ **Filtro ADX** (solo trends fuertes)
- ✅ **Stops más amplios** (menos whipsaws)
- ✅ **Breakeven más rápido** (protege capital)

---

## ⚡ Ejecutar Comparación

```bash
cd ~/BACKTEST
python3 compare_tetr_versions.py
```

**Tiempo estimado:** 2-3 minutos

---

## 📊 Output Esperado

```
================================================================================
📊 COMPREHENSIVE COMPARISON
================================================================================

Pair     Orig Return  Ultra Return  Δ Return  Orig Trades  Ultra Trades  Orig WR  Ultra WR  Orig PF  Ultra PF
BTCUSDT     -1.01%        +2.34%     +3.35%           13            10     30.8%     40.0%     0.82      1.45
ETHUSDT     +1.02%        +2.88%     +1.86%           15            11     40.0%     45.5%     1.28      1.62
SOLUSDT     -2.30%        +1.12%     +3.42%           32            18     34.4%     38.9%     0.90      1.28

================================================================================
📈 SUMMARY
================================================================================

Average Return:
  TETR Original: -0.76%
  TETR Ultra:    +2.11%
  Improvement:   +2.87%

Average Win Rate:
  TETR Original: 35.1%
  TETR Ultra:    41.5%
  Improvement:   +6.4%

Average Profit Factor:
  TETR Original: 1.00
  TETR Ultra:    1.45
  Improvement:   +0.45

Pairs with better performance: 3/3

================================================================================
💡 VERDICT
================================================================================

✅ TETR Ultra is +2.87% better on average!
   ADX filter and wider stops are working.
```

*(Los números arriba son ejemplo, tus resultados reales pueden variar)*

---

## 🔍 Qué Observar

### ✅ Señales de Mejora (BUENO)

1. **Return mejora** en los 3 pares
2. **Profit Factor >1.2** en Ultra (vs <1.0 en Original)
3. **Menos trades** = más selectivo (filtro ADX funciona)
4. **Win Rate sube** 5-10%
5. **Δ Return positivo** en mayoría de pares

**Interpretación:** Las optimizaciones funcionan, ADX está filtrando malos setups

### ⚠️ Señales de Problema (MALO)

1. **Ultra peor** que Original
2. **Profit Factor todavía <1.0**
3. **Cero trades** en algunos pares (demasiado estricto)
4. **Win Rate baja** más

**Interpretación:** Período probablemente muy lateral, incluso con filtros no hay buenos trends

---

## 🎯 Qué Hacer Después

### Si Ultra MEJORA (+2% o más)

1. **Validar en otro período:**
   ```python
   # Edita compare_tetr_versions.py línea 18
   DAYS_BACK = 90  # Probar 3 meses
   ```

2. **Probar en 1h timeframe:**
   ```python
   # Línea 17
   TIMEFRAME = '1h'  # Señales más limpias
   ```

3. **Considerar paper trading** si:
   - Return >3% en 60 días
   - Profit Factor >1.3
   - Consistente en múltiples períodos

### Si Ultra NO MEJORA (<0% todavía)

1. **Probar período diferente:**
   - El mercado puede haber estado muy lateral
   - Cambia fechas y re-testa

2. **Ajustar ADX threshold:**
   ```python
   # Edita strategies/tetr_ultra.py línea 34
   'min_adx': 20,  # En vez de 25 (más permisivo)
   ```

3. **Probar 1h timeframe:**
   ```python
   # Línea 17 en compare_tetr_versions.py
   TIMEFRAME = '1h'
   ```

4. **Analizar trades individuales:**
   ```bash
   # Ver mejores trades de Ultra
   python3 -c "
   import pandas as pd
   df = pd.read_csv('reports/tetr_ultra_BTCUSDT_15m_*/trades.csv')
   print(df.nlargest(10, 'pnl')[['entry_time', 'pnl', 'exit_reason']])
   "
   ```

---

## 🔧 Ajustes Rápidos

### Si Ultra tiene 0 trades (demasiado estricto)

**Opción 1: Bajar ADX threshold**
```python
# strategies/tetr_ultra.py línea 34
'min_adx': 20,  # En vez de 25
```

**Opción 2: Desactivar ADX temporalmente**
```python
# Línea 33
'use_adx_filter': False,
```

### Si Ultra tiene muchos trades pero baja WR

**Opción 1: Subir ADX (más selectivo)**
```python
'min_adx': 30,  # Solo trends muy fuertes
```

**Opción 2: Stops más amplios**
```python
# Línea 38
'stop_atr_buffer': 1.0,  # En vez de 0.8
```

---

## 📁 Archivos Generados

Después de correr verás:

```
reports/
├── tetr_BTCUSDT_15m_*/          # Original
├── tetr_ultra_BTCUSDT_15m_*/    # Ultra (NEW)
├── tetr_ETHUSDT_15m_*/
├── tetr_ultra_ETHUSDT_15m_*/
├── tetr_SOLUSDT_15m_*/
└── tetr_ultra_SOLUSDT_15m_*/
```

Cada carpeta `tetr_ultra_*` contiene:
- `summary.json` - Métricas
- `trades.csv` - Lista de trades
- `equity_curve.csv` - Evolución del capital

---

## 🔬 Análisis Profundo (Opcional)

Si quieres analizar por qué Ultra es mejor/peor:

```bash
# Comparar exit reasons
python3 -c "
import pandas as pd

# Original
orig = pd.read_csv('reports/tetr_BTCUSDT_15m_*/trades.csv')
print('ORIGINAL Exit Reasons:')
print(orig['exit_reason'].value_counts())

# Ultra
ultra = pd.read_csv('reports/tetr_ultra_BTCUSDT_15m_*/trades.csv')
print('\nULTRA Exit Reasons:')
print(ultra['exit_reason'].value_counts())
"

# Ver distribución de R-multiples
python3 -c "
import pandas as pd

orig = pd.read_csv('reports/tetr_BTCUSDT_15m_*/trades.csv')
ultra = pd.read_csv('reports/tetr_ultra_BTCUSDT_15m_*/trades.csv')

print(f'Original Avg R: {orig[\"r_multiple\"].mean():.2f}')
print(f'Ultra Avg R: {ultra[\"r_multiple\"].mean():.2f}')
"
```

---

## ❓ FAQ

**Q: ¿Por qué Ultra tiene menos trades?**
A: El filtro ADX rechaza trends débiles. Esto es intencional - calidad sobre cantidad.

**Q: ¿Qué pasa si Ultra es peor?**
A: El período puede haber sido muy lateral. Prueba otro período o timeframe 1h.

**Q: ¿Puedo ajustar los parámetros de Ultra?**
A: Sí, edita `strategies/tetr_ultra.py` líneas 28-44.

**Q: ¿Cuánto mejor debe ser Ultra para considerar exitoso?**
A: Al menos +2% mejora en average return y PF >1.2 en mayoría de pares.

**Q: ¿Debo usar Ultra o Original?**
A: Si Ultra mejora en 60 y 90 días, usa Ultra. Si no, el mercado puede no tener suficientes trends fuertes.

---

## 📞 Troubleshooting

### "Cannot connect to Binance"
```bash
# Los datos ya están en cache, debería funcionar
# Si no, verifica:
ls -lh data/binance/*/15m.parquet
```

### "Module not found"
```bash
pip3 install pandas numpy aiohttp ccxt
```

### "No trades for Ultra"
ADX filter demasiado estricto. Baja threshold a 20 o desactiva.

---

**Creado:** 14 Nov 2024
**Test:** TETR Original vs TETR Ultra
**Periodo:** Últimos 60 días (Sep 15 - Nov 14, 2025)
**Pares:** BTCUSDT, ETHUSDT, SOLUSDT
**Timeframe:** 15m
