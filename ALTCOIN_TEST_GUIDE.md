# 🚀 Test TETR en Altcoins Volátiles

## 🎯 Por Qué Probar Altcoins

Tu test anterior mostró que **SOL mejoró +5.56%** con TETR Ultra (el único positivo), mientras BTC y ETH empeoraron.

**Hipótesis:** TETR Ultra funciona mejor en **altcoins volátiles** porque:
- ✅ SOL es más volátil que BTC/ETH y fue el único que mejoró
- ✅ Filtro ADX detecta mejor trends fuertes en movimientos explosivos
- ✅ Altcoins tienen más movimientos direccionales claros
- ✅ BTC/ETH son más laterales/consolidación

---

## ⚡ Ejecutar Test de Altcoins

### Paso 1: Descargar Datos de Altcoins

```bash
cd ~/BACKTEST
python3 prepare_altcoin_data.py
```

Esto descarga datos de:
- **AVAXUSDT** (Avalanche) - muy volátil
- **LINKUSDT** (Chainlink) - trends fuertes
- **DOTUSDT** (Polkadot) - buen volumen
- **ADAUSDT** (Cardano) - large cap alt
- **ATOMUSDT** (Cosmos) - volátil

**Tiempo:** 1-2 minutos

### Paso 2: Correr Comparación

```bash
python3 compare_tetr_altcoins.py
```

**Tiempo:** 3-4 minutos

---

## 📊 Qué Esperar

### Escenario A: Ultra Funciona en Altcoins ✅

```
Average Return:
  TETR Original: +0.50%
  TETR Ultra:    +3.20%    ← MUCHO MEJOR
  Improvement:   +2.70%

Pairs with better performance: 4/5 o 5/5
```

**Interpretación:**
- ADX filter funciona mejor en volatilidad alta
- Usa TETR Ultra para altcoins
- Usa TETR Original para BTC/ETH

### Escenario B: Ultra Falla También ❌

```
Average Return:
  TETR Original: -1.20%
  TETR Ultra:    -2.50%
  Improvement:   -1.30%

Pairs with better performance: 1/5 o 0/5
```

**Interpretación:**
- Período muy lateral (Sep-Nov 2024 puede ser consolidación general)
- Necesitas probar otro período o timeframe
- Los cambios de Ultra no ayudan

---

## 🎯 Según Resultado

### Si Ultra MEJORA en Altcoins (>+2%)

**Conclusión:** ADX funciona en alta volatilidad

**Estrategia recomendada:**
```
TETR Ultra  → Altcoins volátiles (AVAX, LINK, SOL, etc)
TETR Original → BTC, ETH (menos volátiles)
```

**Próximo paso:**
```bash
# Validar en período más largo (90 días)
nano compare_tetr_altcoins.py
# Línea 18: DAYS_BACK = 90
python3 compare_tetr_altcoins.py
```

### Si Ultra NO MEJORA (<0%)

**Opción 1: Probar Timeframe 1h**

Menos ruido, señales más limpias:

```bash
nano compare_tetr_altcoins.py
# Línea 17: TIMEFRAME = '1h'

nano prepare_altcoin_data.py
# Línea 17: TIMEFRAME = '1h'

python3 prepare_altcoin_data.py
python3 compare_tetr_altcoins.py
```

**Opción 2: Bajar ADX Threshold**

Filtro menos estricto:

```bash
nano strategies/tetr_ultra.py
# Línea 34: 'min_adx': 20,  # En vez de 25

python3 compare_tetr_altcoins.py
```

**Opción 3: Probar Otro Período**

Puede que Sep-Nov 2024 fue muy lateral:

```bash
nano compare_tetr_altcoins.py
# Línea 18: DAYS_BACK = 90  # 3 meses
# O cambiar rango específico en el código

python3 prepare_altcoin_data.py
python3 compare_tetr_altcoins.py
```

---

## 📈 Interpretando Métricas

### Profit Factor (PF)

- **>1.3**: Excelente (ganas $1.30 por cada $1 perdido)
- **1.0-1.3**: Aceptable
- **<1.0**: Perdiendo

### Win Rate (WR)

Para TETR:
- **>40%**: Muy bueno
- **30-40%**: Aceptable si PF >1.2
- **<30%**: Necesita PF >1.5 para compensar

### Return

- **>3% en 60 días**: Muy bueno (~18% anualizado)
- **1-3%**: Aceptable
- **<0%**: Perdiendo

---

## 🔍 Análisis Profundo (Opcional)

Si quieres ver por qué Ultra funciona mejor/peor en un par específico:

```bash
# Ver trades de AVAX con Ultra
cat reports/tetr_ultra_AVAXUSDT_15m_*/trades.csv | head -20

# Comparar exit reasons
python3 -c "
import pandas as pd

orig = pd.read_csv('reports/tetr_AVAXUSDT_15m_*/trades.csv')
ultra = pd.read_csv('reports/tetr_ultra_AVAXUSDT_15m_*/trades.csv')

print('ORIGINAL Exit Reasons:')
print(orig['exit_reason'].value_counts())
print()
print('ULTRA Exit Reasons:')
print(ultra['exit_reason'].value_counts())
"

# Ver distribución R-multiples
python3 -c "
import pandas as pd

orig = pd.read_csv('reports/tetr_AVAXUSDT_15m_*/trades.csv')
ultra = pd.read_csv('reports/tetr_ultra_AVAXUSDT_15m_*/trades.csv')

print(f'Original Avg R: {orig[\"r_multiple\"].mean():.2f}')
print(f'Ultra Avg R: {ultra[\"r_multiple\"].mean():.2f}')
"
```

---

## 🏆 Mejores Altcoins

El script mostrará al final:

```
🏆 Top 3 Improvements:
   1. AVAXUSDT: +4.52% (-1.20% → +3.32%)
   2. LINKUSDT: +3.88% (+0.50% → +4.38%)
   3. ATOMUSDT: +2.15% (-0.80% → +1.35%)
```

Estos son los pares donde Ultra funciona mejor. Considera:
- Usar Ultra principalmente en estos pares
- Analizar qué tienen en común (volatilidad, trends)
- Optimizar parámetros específicamente para ellos

---

## ❓ FAQ

**Q: ¿Por qué estas altcoins específicas?**
A: Alta volatilidad + buen volumen + diferentes sectores (L1, Oracle, etc)

**Q: ¿Puedo probar otras altcoins?**
A: Sí, edita `VOLATILE_ALTCOINS` en ambos scripts. Ejemplos:
```python
VOLATILE_ALTCOINS = [
    'NEARUSDT',   # Near Protocol
    'FTMUSDT',    # Fantom
    'MATICUSDT',  # Polygon
    'APTUSDT',    # Aptos
    'ARBUSDT',    # Arbitrum
]
```

**Q: ¿Qué pasa si Ultra funciona en altcoins pero no en BTC/ETH?**
A: Es normal. Usa Ultra para alts, Original para BTC/ETH. Son mercados diferentes.

**Q: ¿Cuántos pares deben mejorar para considerar exitoso?**
A: Al menos 3/5 (60%) con mejora >1% cada uno.

**Q: ¿Puedo usar Ultra en paper trading si funciona?**
A: Solo si:
- Mejora >2% en promedio
- PF >1.2 en mayoría de pares
- Validas en período 90 días
- Probaste en timeframe 1h también

---

## 📞 Troubleshooting

### "Cannot connect to Binance"
```bash
# Verifica internet
ping binance.com

# Retry download
python3 prepare_altcoin_data.py
```

### "No data retrieved"
Alguna altcoin puede no tener datos en Binance Futures. Edita la lista:
```bash
nano prepare_altcoin_data.py
# Comenta el par problemático con #
```

### "Module not found"
```bash
pip3 install pandas numpy aiohttp ccxt tabulate
```

---

**Creado:** 14 Nov 2024
**Propósito:** Validar si TETR Ultra funciona mejor en mercados volátiles
**Basado en:** Observación que SOL (+5.56%) fue el único que mejoró con Ultra
