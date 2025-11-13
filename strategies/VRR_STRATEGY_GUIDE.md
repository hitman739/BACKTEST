# Volatility Rejection Reversal (VRR) - Strategy Guide

## Overview

VRR es una estrategia de reversión rápida diseñada para capturar micro-reversiones tras movimientos direccionales extremos en entornos de alta volatilidad.

## Características Principales

### 1. **Detección de Movimientos Extremos**
- Movimiento direccional ≥ 1.5× ATR(14) en las últimas 5 velas
- RSI > 70 (sobrecompra) o < 30 (sobreventa)
- Volumen > 1.5× promedio (20)

### 2. **Candle de Reversión**
- Wick ≥ 30% del rango total
- Cierre dentro del rango de la vela anterior
- Para shorts: upper wick grande (rechazo de buyers)
- Para longs: lower wick grande (rechazo de sellers)

### 3. **Divergencia de Volumen**
- Volumen decreciente en el último empujón
- Indica agotamiento del movimiento
- Confirma que la fuerza compradora/vendedora se está debilitando

### 4. **Market Regime Filters**

#### Volatility Filter
```python
ATR_current ≥ 1.0 × ATR(50)
```
Evita operar en mercados planos.

#### Trend Filter (opcional)
```python
abs(EMA20 - EMA50) / close ≥ 0.5%
```
Evita mercados en rango estrecho.

#### Time Filter (opcional)
```python
12:00 - 22:00 UTC
```
Opera solo en horario de mayor volumen global.

### 5. **Gestión de Salidas Adaptativa**

#### Targets
- **TP1**: 1.8R (50% de la posición)
- **TP2**: 3.0R (resto de la posición)

#### Trailing Stop
- **Activación**: 2.0R de ganancia
- **Distancia**: 0.6R desde el precio actual

#### Salidas Dinámicas
- **Volume Exhaustion**: Si volumen < promedio y RSI cruza 50
- **Counter Candle**: Vela contraria fuerte con alto volumen
- **VWAP Cross**: Precio cruza VWAP en dirección contraria
- **New Impulse**: Nuevo movimiento ≥ 2× ATR en misma dirección

### 6. **Position Sizing Dinámico**

#### Por Calidad del Setup
- **Extreme** (RSI > 75 o < 25 + wick > 60%): Tamaño completo (1.0×)
- **High** (RSI extremo O wick extremo): Tamaño medio (0.75×)
- **Moderate** (condiciones básicas): Tamaño reducido (0.5×)

#### Fórmula Base
```python
risk_amount = equity × 1%
position_size = risk_amount / (entry_price - stop_loss)
position_size = position_size × quality_multiplier
```

### 7. **Stop Loss**
```python
stop_loss = extreme_wick + (ATR × 0.2)
```

Para shorts: Stop por encima del high
Para longs: Stop por debajo del low

## Implementación

### Versión Standard (Filtros Completos)
```python
from strategies.vrr_strategy import VRRStrategy

strategy = VRRStrategy()
```

### Versión Adjusted (Parámetros Realistas)
```python
from strategies.vrr_adjusted import VRRAdjusted

strategy = VRRAdjusted()
```

### Versión Personalizada
```python
from strategies.vrr_strategy import VRRStrategy

config = {
    'name': 'My VRR Custom',
    'directional_move_atr_mult': 1.5,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'volume_spike_mult': 1.5,
    'volume_ratio_min': 1.2,
    'wick_percentage_min': 0.30,
    'time_filter_enabled': True,
    'trading_hours_start': 12,
    'trading_hours_end': 22,
}

strategy = VRRStrategy(config)
```

## Ejecutar Backtest

### SOLUSDT 1m (Recommended)
```bash
python -c "
from engine.backtester import Backtester
from strategies.vrr_adjusted import VRRAdjusted
from engine.metrics import format_metrics_table

strategy = VRRAdjusted()

backtester = Backtester(
    strategy=strategy,
    symbol='SOLUSDT',
    timeframe='1m',
    start_date='2024-10-01',
    end_date='2024-11-13',
    initial_balance=10000,
    leverage=10
)

results = backtester.run()
print(format_metrics_table(results['metrics']))
"
```

### BTCUSDT 5m
```bash
python run_backtest.py \
    --strategy strategies/vrr_adjusted.py \
    --symbol BTCUSDT --timeframe 5m \
    --from 2024-08-01 --to 2024-10-01 \
    --equity 10000 --leverage 5
```

### Otros Pares Volátiles
- ETHUSDT 1m / 5m
- BNBUSDT 1m / 5m
- SOLUSDT 1m / 3m
- AVAXUSDT 1m / 5m

## Optimización de Parámetros

### Timeframe
- **1m**: Máxima frecuencia, requiere ejecución rápida
- **5m**: Balance entre señales y ruido
- **15m**: Setups más limpios pero menos frecuentes

### Leverage
- **1m**: 5-10× (movimientos rápidos)
- **5m**: 3-5× (más tiempo de reacción)
- **15m**: 2-3× (movimientos mayores)

### Ajuste de Sensibilidad

**Más Señales (Trade Frequency ↑)**
```python
{
    'directional_move_atr_mult': 1.3,
    'rsi_overbought': 65,
    'rsi_oversold': 35,
    'volume_spike_mult': 1.2,
    'volume_ratio_min': 1.0,
}
```

**Más Selectivo (Quality ↑)**
```python
{
    'directional_move_atr_mult': 2.0,
    'rsi_overbought': 75,
    'rsi_oversold': 25,
    'volume_spike_mult': 2.0,
    'volume_ratio_min': 2.0,
    'wick_percentage_min': 0.50,
}
```

## Métricas de Evaluación

### Métricas Clave a Monitorear

1. **Win Rate**: Debe estar entre 45-60%
2. **Profit Factor**: Objetivo > 1.3
3. **Avg R-Multiple**: Objetivo > 0.5
4. **Max Drawdown**: Mantener < 15%

### Análisis por Exit Reason

Revisar `exit_reason` en trades.csv:
- **stop_loss**: Si >40% → stops muy ajustados
- **take_profit_2**: Si <20% → dejar correr más
- **vwap_cross**: Si >50% → considerar eliminar filtro VWAP
- **volume_exhaustion**: Indica exhaustion detection funciona

### Análisis por Setup Quality

```
extreme  : Alta calidad, debería tener Win Rate > 60%
high     : Calidad media, Win Rate ~ 50%
moderate : Calidad baja, puede necesitar más filtros
```

## Best Practices

### 1. Walk-Forward Testing
Probar en múltiples períodos:
```python
periods = [
    ('2024-01-01', '2024-03-01'),
    ('2024-03-01', '2024-05-01'),
    ('2024-05-01', '2024-07-01'),
]
```

### 2. Different Market Conditions
- **Trending**: VRR funciona mejor en reversiones de tendencia
- **Ranging**: Puede generar muchas señales falsas
- **High Volatility**: Ideal para VRR
- **Low Volatility**: Considerar desactivar

### 3. Pair Selection
Pares ideales:
- Alta volatilidad intradía (>3% daily)
- Buen volumen (top 20 por market cap)
- Spreads ajustados (<0.05%)

### 4. Ajuste de Horarios
```python
# Asia session (baja volatilidad) - evitar
'trading_hours_start': 0,
'trading_hours_end': 8,

# London + NY overlap (alta volatilidad) - preferir
'trading_hours_start': 12,
'trading_hours_end': 20,
```

## Fail-Safes Implementados

### 1. Timeout
Si no hay progreso en 5 velas → exit

### 2. New Impulse Detection
Si aparece nuevo movimiento ≥ 2× ATR en misma dirección → exit

### 3. VWAP Cross
Precio cruza VWAP contra posición → exit

### 4. Max Position Time
Evita quedarse atrapado en posición perdedora

## Reporting

Cada backtest genera:

### summary.json
```json
{
  "metrics": {
    "total_pnl": -777.60,
    "win_rate_pct": 48.28,
    "profit_factor": 0.51,
    "avg_r_multiple": 0.04
  }
}
```

### trades.csv
Incluye columnas especiales VRR:
- `setup_quality`: extreme / high / moderate
- `rsi`: RSI al momento de entrada
- `atr`: ATR al momento de entrada
- `volume_ratio`: Ratio de volumen
- `wick_pct`: Porcentaje de wick
- `exit_reason`: Razón de salida
- `bars_held`: Duración del trade

## Troubleshooting

### Problema: No Genera Trades

**Diagnóstico:**
```bash
python debug_vrr.py
```

**Soluciones:**
1. Reducir `volume_spike_mult` (de 4.0 a 1.5)
2. Reducir `directional_move_atr_mult` (de 1.8 a 1.3)
3. Ampliar RSI thresholds (70/30 en vez de 74/26)
4. Desactivar trend_filter temporalmente

### Problema: Demasiadas Señales Falsas

**Soluciones:**
1. Aumentar `wick_percentage_min` (de 0.30 a 0.40)
2. Aumentar `volume_ratio_min` (de 1.2 a 2.0)
3. Activar `trend_filter_enabled`
4. Reducir horario de trading (solo overlap sessions)

### Problema: Stops Muy Ajustados

**Solución:**
Aumentar buffer del stop:
```python
# En _calculate_stop_loss
buffer = atr * 0.3  # En vez de 0.2
```

### Problema: No Alcanza TP2

**Solución:**
Reducir TP2:
```python
'tp2_r_mult': 2.5,  # En vez de 3.0
```

## Próximos Pasos

### Mejoras Futuras

1. **Multi-Timeframe Confirmation**
   - Confirmar RSI en 5m y 15m
   - Verificar estructura de precio en TF mayor

2. **ML-Based Quality Assessment**
   - Entrenar modelo para predecir setup quality
   - Usar features: RSI, ATR, volume, hora, etc.

3. **Adaptive Parameters**
   - Ajustar thresholds según volatilidad del mercado
   - Regime detection automático

4. **Delta Volume Integration**
   - Si tienes acceso a orderflow
   - Confirmar absorción en el wick

## Conclusión

VRR es una estrategia avanzada que requiere:
- ✅ Entorno de alta volatilidad
- ✅ Ejecución rápida (especialmente en 1m)
- ✅ Ajuste fino de parámetros por par/timeframe
- ✅ Monitoreo activo de métricas

**Ideal para:**
- Scalping en criptos volátiles
- Capturing reversiones rápidas
- Trading algorítmico automatizado

**No recomendado para:**
- Mercados en rango estrecho
- Pares con bajo volumen
- Trading manual (requiere velocidad)

---

**Desarrollado como parte del sistema de backtesting modular**
**Versión:** 1.0
**Última actualización:** 2024-11-13
