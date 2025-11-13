# Hyperliquid Vault Reverse Engineering System

## 🎯 Objetivo

Sistema completo de ingeniería inversa para extraer la estrategia exacta que usa cualquier vault de Hyperliquid, basándose únicamente en sus trades históricos.

## 📋 ¿Qué hace el sistema?

Este sistema analiza completamente un vault y reconstruye su estrategia de trading con precisión:

### 1. **Recolección de Datos**
- Descarga todos los trades del vault desde Hyperliquid API
- Obtiene datos OHLCV (intenta Binance primero, fallback a Hyperliquid)
- Reconstruye posiciones completas con entry/exit/PnL

### 2. **Feature Engineering Avanzado (100+ features)**
- **Indicadores Técnicos**: EMA 9/20/50/200, RSI, ATR, Bollinger Bands, VWAP
- **Volatilidad**: Realizada (lookback 20/50/100), ATR%, percentiles
- **Tendencia**: EMA slopes, regime detection (trend vs range)
- **Volumen**: Volumen relativo, desviación vs VWAP
- **Microestructura**: Horarios, sesiones, frecuencia de trades
- **Métricas de Posición**: MFE, MAE, R-multiples, holding time patterns

### 3. **Análisis de Patrones con ML**
- **Decision Trees**: Reglas interpretables
- **Random Forests**: Feature importance
- **Clustering**: Detección de regímenes de estrategia
- **Correlaciones**: Features más predictivos
- **Análisis por Lado**: Patrones LONG vs SHORT separados

### 4. **Extracción de Reglas Precisas**
Genera reglas ejecutables:
- **Entry**: Condiciones exactas (ej: "LONG cuando EMA20 > EMA50 AND RSI < 35 AND Price > VWAP")
- **Exit**: Stop loss, take profit, trailing stop, time-based
- **Sizing**: Fijo, adaptativo, basado en volatilidad
- **Timing**: Horas activas, sesiones preferidas
- **Risk Management**: Win rate esperado, R-multiples, regímenes preferidos

### 5. **Validación**
- Compara equity curve inferida vs vault original
- Métricas de similitud (correlación, direction accuracy)
- Recomendaciones para mejorar precisión

## 🚀 Uso Rápido

### Instalación de dependencias

```bash
pip install pandas numpy scikit-learn requests pyarrow
```

### Ejecutar análisis completo

```bash
cd ~/Documents/BACKTEST

python3 reverse_engineer_vault_complete.py \
  --vault 0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b \
  --symbol HYPE \
  --timeframe 5m
```

### Parámetros

- `--vault`: Dirección del vault de Hyperliquid (requerido)
- `--symbol`: Símbolo de trading (default: HYPE)
- `--timeframe`: Timeframe para OHLCV (1m, 5m, 15m, 1h, 4h, 1d)

## 📊 Outputs

El sistema genera todos los archivos en `reports/reverse_engineering/<vault_id>/`:

### Archivos Principales

1. **MASTER_REPORT.json**
   - Análisis completo en un solo archivo
   - Resumen de todas las fases
   - Perfecto para revisión rápida

2. **extracted_rules.json**
   - **EL MÁS IMPORTANTE**
   - Reglas precisas de trading listas para implementar
   - Incluye:
     * Entry conditions (LONG/SHORT con thresholds exactos)
     * Exit rules (SL/TP/trailing)
     * Sizing rules
     * Timing filters
     * Risk management

3. **strategy_summary.txt**
   - Versión legible para humanos de las reglas
   - Formato clean para revisión rápida

4. **pattern_analysis_complete.json**
   - Análisis ML completo
   - Feature importance
   - Correlaciones
   - Clusters detectados

5. **validation_report.json**
   - Métricas de validación
   - Comparación de performance
   - Recomendaciones

### Archivos de Datos

6. **positions_with_features.parquet**
   - Dataset completo con 100+ features
   - Útil para análisis custom

7. **positions.parquet**
   - Posiciones reconstruidas básicas

8. **feature_summary.csv**
   - Resumen estadístico de todas las features

## 📖 Ejemplo de Salida

### Strategy Summary Output

```
======================================================================
EXTRACTED STRATEGY RULES
======================================================================

📊 STRATEGY TYPE: Scalping
   Win Rate: 100.0%
   Directional Bias: SHORT
   Avg Holding Time: 21 minutes

📈 ENTRY RULES:
  SHORT (100.0% WR):
    - EMA20 < EMA50
    - Price < EMA20
    - RSI > 70
    - Price > VWAP
    - High Volume

📉 EXIT RULES:
  Stop Loss: 0.85% (high confidence)
  Take Profit: 1.25% (medium confidence)
  Trailing Stop: Enabled (activate at 1.5R)

📏 POSITION SIZING:
  Type: volatility_adjusted
  Base Size: 4.50

⏰ TIMING RULES:
  Active Hours: [17, 14, 10, 9, 16]
  Preferred Sessions: ['us', 'europe']
```

## 🔍 Interpretación de Resultados

### 1. Metadata
- **Strategy Type**: HFT/Scalping/Intraday/Swing según frecuencia de trades
- **Win Rate**: % de trades ganadores
- **Directional Bias**: Si prefiere LONG, SHORT, o neutral

### 2. Entry Rules
Para cada lado (LONG/SHORT):
- **Conditions**: Lista de condiciones que deben cumplirse
- **Thresholds**: Valores exactos de cada feature importante
- **Win Rate**: % de éxito de este setup específico

### 3. Exit Rules
- **Stop Loss**: % o ATR multiples
- **Take Profit**: Target de ganancia
- **Trailing Stop**: Si activa trailing después de cierto profit
- **Time Exit**: Si cierra por tiempo máximo

### 4. Sizing Rules
- **Fixed**: Tamaño constante
- **Volatility Adjusted**: Inverso a volatilidad (más vol = menos size)
- **Volatility Scaled**: Proporcional a volatilidad
- **Adaptive**: Varía según otros factores

### 5. Timing Rules
- **Active Hours**: Horas UTC con más actividad
- **Preferred Sessions**: Asia/Europe/US
- **Min Time Between Trades**: Evita over-trading

## 🎓 Workflow Recomendado

### Paso 1: Ejecutar Análisis
```bash
python3 reverse_engineer_vault_complete.py \
  --vault <vault_address> \
  --symbol <symbol> \
  --timeframe 5m
```

### Paso 2: Revisar Strategy Summary
```bash
cat reports/reverse_engineering/<vault_id>/strategy_summary.txt
```

### Paso 3: Analizar Reglas Detalladas
```bash
cat reports/reverse_engineering/<vault_id>/extracted_rules.json | jq .
```

### Paso 4: Validar Performance
```bash
cat reports/reverse_engineering/<vault_id>/validation_report.txt
```

### Paso 5: Implementar Estrategia

Usa las reglas extraídas para:
1. Crear una clase de estrategia custom
2. Implementar las condiciones de entry/exit
3. Configurar risk management

Ejemplo:

```python
from engine.strategy import BaseStrategy

class VaultCloneStrategy(BaseStrategy):
    def __init__(self, config=None):
        # Usa los thresholds de extracted_rules.json
        self.ema_entry_threshold = 0.005
        self.rsi_entry_threshold = 70
        self.stop_loss_pct = 0.85
        self.take_profit_pct = 1.25

    def on_bar(self, bar):
        # Implementa las entry conditions
        if self.should_enter_short(bar):
            self.enter_short(bar, size=self.calculate_size(bar))

    def should_enter_short(self, bar):
        # Usa las conditions de extracted_rules
        return (
            bar.ema_20 < bar.ema_50 and
            bar.close < bar.ema_20 and
            bar.rsi > 70 and
            bar.close > bar.vwap
        )
```

### Paso 6: Backtest
```python
from engine.backtester import Backtester

backtester = Backtester(
    strategy=VaultCloneStrategy(),
    symbol='HYPE',
    timeframe='5m',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

results = backtester.run()
```

### Paso 7: Comparar con Vault
Compara tus resultados de backtest con la performance del vault original en `validation_report.json`.

## 🔧 Troubleshooting

### Error: "403 Forbidden from Hyperliquid"
**Causa**: IP bloqueada por Hyperliquid
**Solución**: Ejecuta en tu Mac o usa VPN

### Error: "No data for symbol from Binance"
**Causa**: Símbolo no disponible en Binance
**Solución**: El sistema automáticamente usa Hyperliquid OHLCV como fallback

### Error: "Empty entry conditions"
**Causa**: No se obtuvieron datos OHLCV
**Solución**:
1. Verifica que puedes acceder a Hyperliquid API
2. Ejecuta en Mac si estás en servidor bloqueado
3. El sistema generará análisis con features no-técnicas

### Pocas features generadas
**Causa**: OHLCV no disponible
**Impacto**: Solo tendrás features de timing/sizing, no técnicas
**Solución**: Usa un vault que opere símbolos en Binance (SOL, BTC, ETH)

## 📈 Casos de Uso

### 1. Clonar Estrategia de Vault Exitoso
- Analiza vault con buen track record
- Extrae reglas
- Implementa en tu propia estrategia
- Backtest y valida

### 2. Entender Vault Antes de Invertir
- Analiza vault antes de depositar fondos
- Verifica si la estrategia tiene sentido
- Chequea risk management
- Valida consistencia

### 3. Comparar Múltiples Vaults
- Ejecuta análisis en varios vaults
- Compara extracted_rules.json
- Identifica mejores estrategias
- Combina elementos de varios

### 4. Aprender de Traders Exitosos
- Analiza vaults top performers
- Estudia sus patrones
- Identifica features importantes
- Mejora tu propia estrategia

## 🎯 Métricas de Calidad

### Correlation > 0.7
✅ Excelente - Estrategia muy similar

### Correlation 0.5-0.7
⚠️ Buena - Captura patrones principales

### Correlation < 0.5
❌ Pobre - Revisa reglas extraídas

### Direction Accuracy > 75%
✅ Entry logic correcto

### Direction Accuracy < 60%
❌ Entry signals incorrectos

## 💡 Tips Avanzados

### 1. Análisis Multi-Timeframe
Ejecuta el análisis en múltiples timeframes:
```bash
for tf in 1m 5m 15m; do
    python3 reverse_engineer_vault_complete.py --vault <addr> --timeframe $tf
done
```

### 2. Análisis Longitudinal
Analiza el mismo vault en diferentes períodos:
- Últimos 7 días
- Últimos 30 días
- Últimos 90 días

Compara si la estrategia cambió.

### 3. Feature Importance Analysis
Revisa `pattern_analysis_complete.json` → `feature_importance` para ver qué indicadores son MÁS importantes para el vault.

### 4. Cluster Analysis
Chequea si el vault tiene múltiples "regímenes" de trading en `pattern_analysis_complete.json` → `clusters`.

## 📚 Archivos del Sistema

```
reverse_engineering/
├── data/
│   ├── vault_data_interface.py       # Fetch trades from Hyperliquid
│   ├── position_reconstructor.py     # Reconstruct positions
│   ├── ohlcv_aligner.py              # Align with OHLCV data
│   └── hyperliquid_loader.py         # Hyperliquid OHLCV loader
├── features/
│   ├── feature_engineering.py         # Basic features
│   └── advanced_feature_engineering.py # 100+ features
├── analysis/
│   ├── pattern_analysis.py            # Basic ML analysis
│   └── advanced_pattern_analysis.py   # Deep ML analysis
├── extraction/
│   ├── rule_extraction.py             # Basic rule extraction
│   └── precise_rule_extractor.py      # Precise rules
└── validation/
    └── equity_curve_validator.py      # Performance validation

reverse_engineer_vault_complete.py     # 🎯 MAIN SCRIPT
```

## 🚀 Siguiente Nivel

Una vez que tengas las reglas extraídas:

1. **Optimización**: Usa grid search para optimizar thresholds
2. **Walk-Forward**: Valida en períodos out-of-sample
3. **Paper Trading**: Prueba en live sin riesgo
4. **Portfolio**: Combina múltiples estrategias de vaults
5. **Auto-Trading**: Implementa ejecución automática

## ⚠️ Disclaimer

Este sistema extrae patrones históricos. No garantiza performance futura. Siempre:
- Backtest exhaustivamente
- Paper trade primero
- Empieza con size pequeño
- Monitorea constantemente
- Ten stop loss en cuenta

## 🤝 Soporte

Si encuentras problemas:
1. Revisa este README
2. Chequea los logs de ejecución
3. Verifica validation_report.json para recomendaciones
4. Analiza pattern_analysis_complete.json para insights

---

**¡Listo para extraer estrategias de los mejores traders de Hyperliquid!** 🎉
