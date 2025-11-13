# 📋 PASO A PASO: Análisis de Vault + Backtest

## 🎯 FASE 1: EXTRACCIÓN DE INFORMACIÓN DEL VAULT

### PASO 1: Ejecutar Análisis Completo del Vault

**En tu Mac, navega al directorio:**
```bash
cd ~/Documents/BACKTEST
```

**Ejecuta el análisis completo:**
```bash
python3 reverse_engineer_vault_complete.py \
  --vault 0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b \
  --symbol HYPE \
  --timeframe 5m
```

**Tiempo estimado:** 2-5 minutos

**Output esperado:**
- ✅ Fetch ~803 trades
- ✅ Reconstruct ~146 positions
- ✅ Align with OHLCV (desde Hyperliquid)
- ✅ Generate 100+ features
- ✅ ML analysis complete
- ✅ Rules extracted
- ✅ Reports generated

**Archivos generados en:** `reports/reverse_engineering/0x9b55c8c9/`

---

### PASO 2: Revisar Strategy Summary (Legible)

```bash
cat reports/reverse_engineering/0x9b55c8c9/strategy_summary.txt
```

**Qué buscar:**
- ✅ **Strategy Type**: ¿Es HFT, Scalping, Intraday o Swing?
- ✅ **Win Rate**: % de trades ganadores
- ✅ **Directional Bias**: ¿Prefiere LONG, SHORT o neutral?
- ✅ **Avg Holding Time**: Duración promedio de trades
- ✅ **Entry Rules**: Condiciones para LONG y SHORT
- ✅ **Exit Rules**: Stop Loss, Take Profit, Trailing
- ✅ **Timing Rules**: Horas activas, sesiones preferidas

**Acción:** Anota las reglas principales en un documento

---

### PASO 3: Revisar Reglas Precisas (JSON)

```bash
cat reports/reverse_engineering/0x9b55c8c9/extracted_rules.json | jq .
```

O si no tienes `jq`:
```bash
cat reports/reverse_engineering/0x9b55c8c9/extracted_rules.json
```

**Qué buscar:**

#### 3.1 Entry Rules
```json
"entry_rules": {
  "long": {
    "enabled": true/false,
    "conditions": ["EMA20 > EMA50", "Price > EMA20", ...],
    "thresholds": {
      "feature_name": {
        "winner_value": 0.XX,
        "importance": 0.XX
      }
    }
  },
  "short": { ... }
}
```

**Anota:**
- Condiciones LONG (si enabled=true)
- Condiciones SHORT (si enabled=true)
- Thresholds exactos de cada feature

#### 3.2 Exit Rules
```json
"exit_rules": {
  "stop_loss": {
    "enabled": true,
    "value_pct": 0.85,
    "confidence": "high"
  },
  "take_profit": {
    "enabled": true,
    "value_pct": 1.25,
    "confidence": "medium"
  },
  "trailing_stop": {
    "enabled": true,
    "activation_r": 1.5
  }
}
```

**Anota:**
- Stop Loss %
- Take Profit %
- Si usa trailing stop y cuándo activa

#### 3.3 Sizing Rules
```json
"sizing_rules": {
  "type": "volatility_adjusted",
  "base_size": 4.50,
  "volatility_correlation": -0.65
}
```

**Anota:**
- Tipo de sizing (fixed, adaptive, volatility_adjusted)
- Base size
- Si es adaptativo, cómo ajusta

#### 3.4 Timing Rules
```json
"timing_rules": {
  "active_hours": [17, 14, 10, 9, 16],
  "preferred_sessions": ["us", "europe"],
  "min_minutes_between_trades": 6.5
}
```

**Anota:**
- Horas activas (UTC)
- Sesiones preferidas
- Tiempo mínimo entre trades

---

### PASO 4: Revisar Pattern Analysis (ML Insights)

```bash
cat reports/reverse_engineering/0x9b55c8c9/pattern_analysis_complete.json | jq .
```

**Qué buscar:**

#### 4.1 Feature Importance
```json
"entry_patterns": {
  "feature_importance": [
    {"feature": "rsi_overbought", "importance": 0.35},
    {"feature": "price_above_ema20", "importance": 0.28},
    ...
  ]
}
```

**Acción:** Anota los top 5 features más importantes (importance > 0.10)

#### 4.2 Exit Patterns
```json
"exit_patterns": {
  "mfe_mae_analysis": {
    "avg_mfe_pct": 1.25,
    "avg_mae_pct": 0.85
  }
}
```

**Acción:** Confirma los valores de SL/TP

#### 4.3 Clusters
```json
"clusters": {
  "cluster_profiles": [
    {
      "cluster_id": 0,
      "size": 50,
      "win_rate": 100,
      "avg_holding_mins": 15
    }
  ]
}
```

**Acción:** Si hay múltiples clusters, identifica si el vault tiene diferentes "modos"

---

### PASO 5: Revisar Validation Report

```bash
cat reports/reverse_engineering/0x9b55c8c9/validation_report.txt
```

**Qué buscar:**
- ✅ **Total Trades**: Cuántos trades analizados
- ✅ **Win Rate**: % exacto de ganadores
- ✅ **Total PnL**: Ganancia total del vault
- ✅ **Profit Factor**: Ratio ganancia/pérdida
- ✅ **Avg R-Multiple**: R promedio por trade

**Acción:** Estos son tus benchmarks para comparar el backtest

---

### PASO 6: Crear Dataset de Features (Opcional pero Útil)

```bash
python3 -c "
import pandas as pd
df = pd.read_parquet('reports/reverse_engineering/0x9b55c8c9/positions_with_features.parquet')
print('Total features:', len(df.columns))
print('\nFeature names:')
print(df.columns.tolist())
print('\nFirst position:')
print(df.head(1).T)
"
```

**Acción:** Explora el dataset completo si quieres hacer análisis custom

---

## 🎯 FASE 2: IMPLEMENTAR ESTRATEGIA PARA BACKTEST

### PASO 7: Crear Clase de Estrategia

**Ubicación:** `strategies/vault_clone_hype.py`

```bash
cat > strategies/vault_clone_hype.py << 'EOF'
"""
Vault Clone Strategy - HYPE
Extracted from vault 0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b
"""

from engine.strategy import BaseStrategy


class VaultCloneHYPE(BaseStrategy):
    """
    Strategy cloned from Hyperliquid vault analysis

    Type: Scalping
    Win Rate Target: 100%
    Avg Holding: 21 mins
    Bias: SHORT
    """

    def __init__(self, config: dict = None):
        super().__init__(config)

        # ===== CONFIGURATION FROM EXTRACTED RULES =====
        # TODO: Fill from extracted_rules.json

        # Entry thresholds
        self.ema_short = 20
        self.ema_long = 50
        self.rsi_period = 14
        self.rsi_overbought = 70  # SHORT entry
        self.rsi_oversold = 30     # LONG entry

        # Exit rules
        self.stop_loss_pct = 0.85      # From extracted_rules.json
        self.take_profit_pct = 1.25    # From extracted_rules.json
        self.use_trailing = True       # From extracted_rules.json
        self.trailing_activation_r = 1.5

        # Sizing
        self.base_size = 4.50          # From extracted_rules.json
        self.use_volatility_sizing = True

        # Timing filters
        self.active_hours = [17, 14, 10, 9, 16]  # UTC
        self.preferred_sessions = ['us', 'europe']
        self.min_minutes_between_trades = 6.5

        # Risk management
        self.max_positions = 1

        # Indicators storage
        self.ema_20 = []
        self.ema_50 = []
        self.rsi = []
        self.atr = []
        self.last_trade_time = None

    def initialize(self, historical_data):
        """Calculate indicators"""
        import pandas as pd

        # EMA 20 and 50
        self.ema_20 = historical_data['close'].ewm(span=self.ema_short, adjust=False).mean()
        self.ema_50 = historical_data['close'].ewm(span=self.ema_long, adjust=False).mean()

        # RSI
        delta = historical_data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        self.rsi = 100 - (100 / (1 + rs))

        # ATR
        high_low = historical_data['high'] - historical_data['low']
        high_close = abs(historical_data['high'] - historical_data['close'].shift())
        low_close = abs(historical_data['low'] - historical_data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.atr = tr.rolling(window=14).mean()

    def on_bar(self, bar, index):
        """Called on each new bar"""

        # Get current indicator values
        current_ema_20 = self.ema_20.iloc[index]
        current_ema_50 = self.ema_50.iloc[index]
        current_rsi = self.rsi.iloc[index]
        current_price = bar['close']
        current_hour = bar.name.hour if hasattr(bar, 'name') else None

        # Check timing filter
        if current_hour is not None and current_hour not in self.active_hours:
            return

        # Check time between trades
        if self.last_trade_time is not None:
            time_diff = (bar.name - self.last_trade_time).total_seconds() / 60
            if time_diff < self.min_minutes_between_trades:
                return

        # Check if we have open positions
        if len(self.positions) >= self.max_positions:
            return

        # ===== ENTRY LOGIC =====
        # TODO: Implement based on extracted_rules.json entry_rules

        # SHORT conditions (from analysis)
        short_conditions = (
            current_ema_20 < current_ema_50 and      # Downtrend
            current_price < current_ema_20 and        # Price below EMA20
            current_rsi > self.rsi_overbought         # RSI overbought
            # TODO: Add more conditions from extracted_rules
        )

        # LONG conditions (if enabled)
        long_conditions = (
            current_ema_20 > current_ema_50 and       # Uptrend
            current_price > current_ema_20 and        # Price above EMA20
            current_rsi < self.rsi_oversold           # RSI oversold
            # TODO: Add more conditions from extracted_rules
        )

        # Calculate position size
        size = self.calculate_position_size(bar, index)

        # Enter trades
        if short_conditions:
            self.enter_short(bar, size)
            self.last_trade_time = bar.name if hasattr(bar, 'name') else None

        elif long_conditions:
            self.enter_long(bar, size)
            self.last_trade_time = bar.name if hasattr(bar, 'name') else None

    def calculate_position_size(self, bar, index):
        """Calculate position size based on sizing rules"""

        if not self.use_volatility_sizing:
            return self.base_size

        # Volatility-adjusted sizing (inverse relationship)
        current_atr = self.atr.iloc[index]
        atr_pct = (current_atr / bar['close']) * 100

        # Reduce size when volatility is high
        if atr_pct > 2.0:
            return self.base_size * 0.5
        elif atr_pct > 1.5:
            return self.base_size * 0.75
        else:
            return self.base_size

    def on_exit(self, position, bar, index):
        """Exit logic"""

        current_price = bar['close']
        entry_price = position['entry_price']
        side = position['side']

        # Calculate PnL %
        if side == 'long':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # short
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        # Stop Loss
        if pnl_pct <= -self.stop_loss_pct:
            return True, 'stop_loss'

        # Take Profit
        if pnl_pct >= self.take_profit_pct:
            return True, 'take_profit'

        # Trailing Stop (if enabled and in profit)
        if self.use_trailing and pnl_pct > self.stop_loss_pct * self.trailing_activation_r:
            # Implement trailing logic
            # TODO: Implement based on extracted_rules
            pass

        return False, None
EOF
```

---

### PASO 8: Completar la Estrategia con Reglas Extraídas

**Edita el archivo y completa los TODOs:**

```bash
nano strategies/vault_clone_hype.py
```

**Completa:**

#### 8.1 Entry Conditions
Busca en `extracted_rules.json` → `entry_rules` → `short` → `conditions`

Ejemplo si las condiciones son:
```json
"conditions": [
  "EMA20 < EMA50",
  "Price < EMA20",
  "RSI > 70",
  "Price > VWAP",
  "High Volume"
]
```

Implementa:
```python
short_conditions = (
    current_ema_20 < current_ema_50 and
    current_price < current_ema_20 and
    current_rsi > 70 and
    current_price > current_vwap and  # Necesitas calcular VWAP
    current_volume > current_volume_ma * 1.5  # High volume
)
```

#### 8.2 Exit Rules
Completa valores exactos de `extracted_rules.json` → `exit_rules`:

```python
self.stop_loss_pct = 0.85      # Valor exacto de exit_rules.stop_loss.value_pct
self.take_profit_pct = 1.25    # Valor exacto de exit_rules.take_profit.value_pct
self.trailing_activation_r = 1.5  # Valor de exit_rules.trailing_stop.activation_r
```

#### 8.3 Sizing
Completa de `extracted_rules.json` → `sizing_rules`:

```python
self.base_size = 4.50  # sizing_rules.base_size
self.use_volatility_sizing = True  # Si type = "volatility_adjusted"
```

#### 8.4 Timing
Completa de `extracted_rules.json` → `timing_rules`:

```python
self.active_hours = [17, 14, 10, 9, 16]  # timing_rules.active_hours
self.min_minutes_between_trades = 6.5  # timing_rules.min_minutes_between_trades
```

---

### PASO 9: Agregar Indicadores Adicionales (Si Necesario)

Si las reglas requieren VWAP, Bollinger Bands, etc., agrégalos en `initialize()`:

```python
def initialize(self, historical_data):
    # ... existing code ...

    # VWAP (aproximado)
    typical_price = (historical_data['high'] + historical_data['low'] + historical_data['close']) / 3
    self.vwap = (typical_price * historical_data['volume']).cumsum() / historical_data['volume'].cumsum()

    # Bollinger Bands
    self.bb_middle = historical_data['close'].rolling(window=20).mean()
    bb_std = historical_data['close'].rolling(window=20).std()
    self.bb_upper = self.bb_middle + (2 * bb_std)
    self.bb_lower = self.bb_middle - (2 * bb_std)
```

---

## 🎯 FASE 3: EJECUTAR BACKTEST

### PASO 10: Crear Script de Backtest

```bash
cat > backtest_vault_clone.py << 'EOF'
#!/usr/bin/env python3
"""
Backtest Vault Clone Strategy
"""

from engine.backtester import Backtester
from strategies.vault_clone_hype import VaultCloneHYPE
from datetime import datetime

# Configuration
config = {
    'initial_capital': 10000,
    'commission': 0.0004,  # 0.04% (Hyperliquid taker fee)
    'slippage': 0.0001,
}

# Create strategy
strategy = VaultCloneHYPE(config)

# Create backtester
backtester = Backtester(
    strategy=strategy,
    symbol='HYPE',
    timeframe='5m',
    start_date='2024-11-01',  # Ajusta según el período del vault
    end_date='2024-11-13',
    initial_capital=config['initial_capital'],
    data_source='hyperliquid'  # Usa Hyperliquid data
)

print("Starting backtest...")
print("=" * 70)

# Run backtest
results = backtester.run()

# Print results
print("\n" + "=" * 70)
print("BACKTEST RESULTS")
print("=" * 70)
print(f"Total Trades: {results['total_trades']}")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Total PnL: ${results['total_pnl']:.2f}")
print(f"Final Capital: ${results['final_capital']:.2f}")
print(f"Return: {results['return_pct']:.2f}%")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Profit Factor: {results['profit_factor']:.2f}")
print(f"Avg Trade: ${results['avg_trade_pnl']:.2f}")
print("=" * 70)

# Save results
backtester.save_results('reports/backtest_vault_clone_hype.json')
print(f"\n💾 Results saved to: reports/backtest_vault_clone_hype.json")
EOF

chmod +x backtest_vault_clone.py
```

---

### PASO 11: Ejecutar Backtest

```bash
python3 backtest_vault_clone.py
```

**Output esperado:**
```
Starting backtest...
======================================================================
Loading HYPE 5m data from Hyperliquid...
✅ Loaded 3456 bars
Running backtest with VaultCloneHYPE...
Progress: 100%
======================================================================

======================================================================
BACKTEST RESULTS
======================================================================
Total Trades: 145
Win Rate: 98.62%
Total PnL: $1,245.50
Final Capital: $11,245.50
Return: 12.45%
Max Drawdown: -2.34%
Sharpe Ratio: 2.8
Profit Factor: 12.5
Avg Trade: $8.59
======================================================================
```

---

## 🎯 FASE 4: COMPARAR CON VAULT ORIGINAL

### PASO 12: Comparar Resultados

**Abre los dos archivos:**

```bash
# Vault original
cat reports/reverse_engineering/0x9b55c8c9/validation_report.txt

# Tu backtest
cat reports/backtest_vault_clone_hype.json
```

**Compara:**

| Métrica | Vault Original | Tu Backtest | Diferencia |
|---------|---------------|-------------|------------|
| Total Trades | 146 | ??? | ??? |
| Win Rate | 100% | ??? | ??? |
| Avg PnL/Trade | $XXX | ??? | ??? |
| Avg Holding Time | 21 mins | ??? | ??? |
| Profit Factor | XXX | ??? | ??? |

**Métricas de Calidad:**

- ✅ **Win Rate diff < 5%** = Excelente
- ✅ **Trade count diff < 20%** = Bueno
- ✅ **Profit factor similar** = Reglas correctas
- ⚠️ **Win rate diff > 10%** = Revisar entry conditions
- ⚠️ **Trade count muy diferente** = Revisar timing filters

---

### PASO 13: Ajustar si es Necesario

**Si Win Rate es muy diferente:**

1. Revisa entry conditions en `extracted_rules.json`
2. Verifica que todos los thresholds estén correctos
3. Chequea timing filters (active_hours)

**Si Trade Count es muy diferente:**

1. Revisa `min_minutes_between_trades`
2. Chequea filtros de sesión
3. Verifica que OHLCV data esté completa

**Si Profit Factor es diferente:**

1. Revisa Stop Loss y Take Profit %
2. Verifica trailing stop logic
3. Chequea comisiones y slippage

**Comando para re-ejecutar:**
```bash
# Después de ajustar strategies/vault_clone_hype.py
python3 backtest_vault_clone.py
```

---

### PASO 14: Generar Reporte de Comparación

```bash
cat > generate_comparison_report.py << 'EOF'
#!/usr/bin/env python3
"""Generate comparison report between vault and backtest"""

import json

# Load vault performance
with open('reports/reverse_engineering/0x9b55c8c9/validation_report.json') as f:
    vault_data = json.load(f)

# Load backtest results
with open('reports/backtest_vault_clone_hype.json') as f:
    backtest_data = json.load(f)

# Extract metrics
vault_perf = vault_data['vault_performance']
bt_perf = backtest_data

# Calculate differences
wr_diff = bt_perf['win_rate'] - vault_perf['win_rate']
trades_diff = bt_perf['total_trades'] - vault_perf['total_trades']
pf_diff = bt_perf['profit_factor'] - vault_perf['profit_factor']

# Generate report
report = f"""
{'=' * 70}
VAULT vs BACKTEST COMPARISON REPORT
{'=' * 70}

📊 VAULT PERFORMANCE (Original):
   Total Trades: {vault_perf['total_trades']}
   Win Rate: {vault_perf['win_rate']:.2f}%
   Total PnL: ${vault_perf['total_pnl']:.2f}
   Profit Factor: {vault_perf['profit_factor']:.2f}
   Avg Holding: {vault_perf['avg_holding_mins']:.0f} mins

🔬 BACKTEST PERFORMANCE (Cloned):
   Total Trades: {bt_perf['total_trades']}
   Win Rate: {bt_perf['win_rate']:.2f}%
   Total PnL: ${bt_perf['total_pnl']:.2f}
   Profit Factor: {bt_perf['profit_factor']:.2f}
   Max Drawdown: {bt_perf['max_drawdown']:.2f}%

📈 DIFFERENCES:
   Win Rate: {wr_diff:+.2f}%
   Trade Count: {trades_diff:+d}
   Profit Factor: {pf_diff:+.2f}

🎯 SIMILARITY SCORE:
   Correlation: {100 - abs(wr_diff) - abs(trades_diff/vault_perf['total_trades']*100):.1f}%

💡 VERDICT:
"""

if abs(wr_diff) < 5 and abs(trades_diff) < vault_perf['total_trades'] * 0.2:
    report += "   ✅ EXCELLENT - Strategy closely matches vault!\n"
elif abs(wr_diff) < 10 and abs(trades_diff) < vault_perf['total_trades'] * 0.3:
    report += "   ✅ GOOD - Strategy captures main patterns.\n"
else:
    report += "   ⚠️  NEEDS IMPROVEMENT - Review entry/exit rules.\n"

report += "\n" + "=" * 70

print(report)

# Save report
with open('reports/COMPARISON_REPORT.txt', 'w') as f:
    f.write(report)

print("\n💾 Report saved to: reports/COMPARISON_REPORT.txt")
EOF

python3 generate_comparison_report.py
```

---

### PASO 15: Análisis Final y Decisión

```bash
cat reports/COMPARISON_REPORT.txt
```

**Si el resultado es EXCELLENT o GOOD:**
- ✅ La estrategia está correctamente extraída
- ✅ Procede a paper trading
- ✅ Considera optimización fina de parámetros

**Si el resultado es NEEDS IMPROVEMENT:**
- ⚠️ Revisa `pattern_analysis_complete.json` para features importantes
- ⚠️ Verifica que todos los thresholds estén correctos
- ⚠️ Considera que el vault puede tener información que no capturaste (order flow, latencia)

---

## 📊 CHECKLIST FINAL

### Análisis del Vault ✅
- [ ] Ejecutado `reverse_engineer_vault_complete.py`
- [ ] Revisado `strategy_summary.txt`
- [ ] Revisado `extracted_rules.json`
- [ ] Revisado `pattern_analysis_complete.json`
- [ ] Revisado `validation_report.txt`
- [ ] Anotadas reglas principales

### Implementación ✅
- [ ] Creada clase `VaultCloneHYPE`
- [ ] Implementadas condiciones de entrada LONG
- [ ] Implementadas condiciones de entrada SHORT
- [ ] Configurado Stop Loss correcto
- [ ] Configurado Take Profit correcto
- [ ] Implementado trailing stop (si aplica)
- [ ] Configurado position sizing
- [ ] Implementados timing filters
- [ ] Agregados todos los indicadores necesarios

### Backtest ✅
- [ ] Ejecutado backtest completo
- [ ] Comparados resultados con vault
- [ ] Win rate similar (diff < 10%)
- [ ] Trade count similar (diff < 30%)
- [ ] Generado comparison report
- [ ] Decisión tomada sobre próximos pasos

---

## 🎉 PRÓXIMO NIVEL

Una vez completados todos los pasos:

1. **Optimización**: Usa grid search para optimizar thresholds
2. **Walk-Forward**: Valida en datos out-of-sample
3. **Paper Trading**: Prueba en tiempo real sin riesgo
4. **Live Trading**: Empieza con size pequeño

---

## 🆘 SOPORTE

Si tienes problemas en algún paso:
- Revisa los logs de ejecución
- Chequea que todos los archivos existan
- Verifica que los datos OHLCV estén disponibles
- Compara tus implementaciones con `extracted_rules.json`

**¡Ahora ejecuta paso a paso y extrae la estrategia del vault!** 🚀
