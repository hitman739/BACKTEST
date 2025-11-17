# Hyperliquid Copy Trading Simulator v3.0

Sistema de simulación de copy trading proporcional usando datos reales de Hyperliquid.

## 🎯 Objetivo

Simular cómo habría ido una cuenta de **10,000 USDT** copiando PROPORCIONALMENTE lo que hace un trader de Hyperliquid.

- ✅ Usa datos REALES de Hyperliquid (fills, posiciones, precios)
- ✅ Solo simula trades desde que presionas "Start simulation"
- ✅ Copia el mismo % de riesgo que el trader
- ✅ Sin fees ni funding (se añadirán después)

---

## 🔑 Conceptos Clave

### 1. Equity Inicial Fijo

Cada simulación empieza SIEMPRE con:
```
equity_sim_inicial = 10,000 USDT
```

No depende del equity real del trader. Es fijo para todas las simulaciones.

### 2. Momento de Inicio

Cuando presionas "Start simulation" para una wallet:
- Se guarda `start_time = ahora`
- Se borran estados anteriores de esa wallet
- Solo se procesan fills con `timestamp >= start_time`
- **NUNCA** se incluyen trades anteriores

### 3. Copiado Proporcional Considerando Leverage del Trader

La clave del sistema: **copiar el mismo % de MARGEN usado por el trader**.

⚠️ **IMPORTANTE**:
- El leverage multiplica el notional, pero NO el riesgo real
- El riesgo real es el **margen usado** = notional / leverage
- La **simulación SIEMPRE opera con leverage 1x** (sin apalancamiento)
- El **sizing** se basa en el margin del trader (considerando su leverage)

Cuando el trader abre un trade:

```python
# 1. Calcular notional del trader
notional_trader = abs(size_trader * price_fill)

# 2. Obtener leverage del trader (de Hyperliquid API)
leverage_trader = [leverage de la posición del trader]

# 3. Calcular MARGEN USADO por el trader (dinero real en riesgo)
margin_trader = notional_trader / leverage_trader

# 4. Obtener equity del trader
equity_trader = [de Hyperliquid API]

# 5. Calcular % de riesgo basado en MARGEN
risk_frac = margin_trader / equity_trader

# 6. Aplicar MISMO % de riesgo a la simulación (SIN leverage)
notional_sim = risk_frac * equity_sim_actual
size_sim = notional_sim / price_fill
```

**Ejemplo con Trader usando Leverage 10x:**
- **Trader**:
  - Equity: $3,000,000
  - Abre: 50 BTC @ $100k = $5M notional
  - **Leverage: 10x**
  - **Margen usado**: $5M / 10 = $500k
  - **Risk %**: $500k / $3M = 16.67%

- **Simulación** (sin leverage):
  - Equity: $10,000
  - **Risk %**: 16.67% (mismo que el trader)
  - **Notional**: $10k * 16.67% = **$1,667**
  - **Size**: $1,667 / $100k = **0.01667 BTC**
  - **Leverage: 1x** (sin apalancamiento)

**Verificación:**
- Trader arriesga 16.67% de su equity ($500k de $3M)
- Simulación arriesga 16.67% de su equity ($1,667 de $10k)
- **Mismo riesgo relativo, sin usar leverage en la simulación**

**Beneficios:**
- ✅ PnL realistas (proporcionales al riesgo del trader)
- ✅ Sin riesgo de liquidación en la simulación
- ✅ Más seguro (no usa leverage)
- ✅ Refleja el verdadero riesgo del trader

### 4. Gestión de Posiciones

Para cada símbolo, la simulación mantiene:
- `size_sim` - Tamaño de la posición simulada (basado en margin del trader)
- `avg_entry_price_sim` - Precio medio de entrada

Acciones:
- **Aumentar posición**: Recalcula `avg_entry_price_sim` como promedio ponderado
- **Reducir posición**: Calcula `realized_pnl_sim` sobre la parte cerrada
- **Cerrar posición**: `realized_pnl_sim` y limpia posición

Nota: La simulación SIEMPRE opera con leverage 1x (sin apalancamiento)

### 5. PnL y Equity (SIN FEES)

La simulación mantiene:

```python
# PnL realizado (de posiciones cerradas)
realized_pnl_sim = sum(pnl_de_cada_cierre)

# PnL no realizado (de posiciones abiertas)
unrealized_pnl_sim = sum(
    size_sim * (mark_price - avg_entry_price_sim)
    for cada posición abierta
)

# PnL total
pnl_total_sim = realized_pnl_sim + unrealized_pnl_sim

# Equity actual
equity_sim_actual = 10,000 + pnl_total_sim
```

**NO se restan fees ni funding** en esta versión.

### 6. Actualización en Tiempo Real

- Proceso en background cada 5 segundos:
  - Consulta fills del trader vía Hyperliquid API
  - Consulta precios mark para símbolos con posiciones
  - Actualiza state de la simulación
  - Recalcula PnL y equity

---

## 🚀 Uso

### Iniciar el Backend

```bash
cd hyperliquid-copytrade/backend
./start_simulator.sh
```

El servidor estará disponible en: `http://localhost:8000`

Documentación automática: `http://localhost:8000/docs`

### API Endpoints

#### 1. POST /sim/start

Iniciar simulación de una wallet.

**Request:**
```bash
curl -X POST http://localhost:8000/sim/start \
  -H "Content-Type: application/json" \
  -d '{"wallet": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"}'
```

**Response:**
```json
{
  "success": true,
  "message": "Simulation started for 0x...",
  "wallet": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b",
  "start_time": 1700000000.0,
  "equity_sim_initial": 10000.0,
  "trader_equity": 3250000.0
}
```

**Acción:**
- Registra la wallet para simulación
- Guarda `start_time = ahora`
- Inicializa `equity_sim_actual = 10,000`
- Obtiene equity actual del trader

#### 2. POST /sim/stop

Detener simulación de una wallet.

**Request:**
```bash
curl -X POST http://localhost:8000/sim/stop \
  -H "Content-Type: application/json" \
  -d '{"wallet": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"}'
```

**Response:**
```json
{
  "success": true,
  "message": "Simulation stopped for 0x...",
  "wallet": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"
}
```

#### 3. GET /sim/snapshot

Obtener estado actual de una simulación.

**Request:**
```bash
curl "http://localhost:8000/sim/snapshot?wallet=0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"
```

**Response:**
```json
{
  "wallet": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b",
  "start_time": 1700000000.0,
  "equity_sim_actual": 10523.45,
  "pnl_total_sim": 523.45,
  "pnl_pct_sim": 5.23,
  "realized_pnl_sim": 345.20,
  "unrealized_pnl_sim": 178.25,
  "open_positions": [
    {
      "symbol": "BTC",
      "side": "long",
      "size_sim": 0.015,
      "avg_entry_price_sim": 95000.0,
      "mark_price": 96500.0,
      "unrealized_pnl_pos": 22.50
    },
    {
      "symbol": "ETH",
      "side": "short",
      "size_sim": 2.5,
      "avg_entry_price_sim": 3500.0,
      "mark_price": 3438.0,
      "unrealized_pnl_pos": 155.00
    }
  ],
  "trades_count_sim": 12
}
```

**Campos:**
- `equity_sim_actual`: Equity actual simulado
- `pnl_total_sim`: PnL total (realizado + no realizado)
- `pnl_pct_sim`: PnL en porcentaje
- `realized_pnl_sim`: PnL de posiciones cerradas
- `unrealized_pnl_sim`: PnL de posiciones abiertas
- `open_positions`: Lista de posiciones abiertas con detalles
- `trades_count_sim`: Número de trades simulados

#### 4. GET /sim/wallets

Listar todas las simulaciones activas.

**Request:**
```bash
curl http://localhost:8000/sim/wallets
```

**Response:**
```json
{
  "count": 3,
  "wallets": [
    {
      "wallet": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b",
      "equity_sim_actual": 10523.45,
      "pnl_total_sim": 523.45,
      "pnl_pct_sim": 5.23,
      "trades_count_sim": 12,
      "start_time": 1700000000.0
    },
    {
      "wallet": "0xabc...",
      "equity_sim_actual": 9850.00,
      "pnl_total_sim": -150.00,
      "pnl_pct_sim": -1.50,
      "trades_count_sim": 8,
      "start_time": 1700001000.0
    }
  ]
}
```

---

## 📊 Flujo de Datos

```
Usuario presiona "Start simulation"
    ↓
POST /sim/start
    ↓
SimulatorEngine crea WalletSimulation
    ↓ (cada 5 segundos)
Background loop:
  1. Consulta fills del trader (Hyperliquid API)
  2. Filtra fills con timestamp >= start_time
  3. Procesa cada fill:
     - Calcula risk_frac del trader
     - Aplica mismo risk_frac a la simulación
     - Actualiza posiciones simuladas
  4. Consulta mark prices para símbolos con posiciones
  5. Recalcula unrealized PnL
    ↓
GET /sim/snapshot
    ↓
Frontend muestra estado actual
```

---

## 🔍 Ejemplo Detallado

### Trader Original

- Equity: $3,000,000
- Abre long BTC: 5 BTC @ $95,000 = $475,000 notional
- **Leverage: 10x**
- **Margen usado**: $475k / 10 = $47,500
- **Risk %**: $47,500 / $3M = 1.58% de su equity

### Simulación

**Estado inicial:**
- `equity_sim_inicial = $10,000`

**Al detectar el fill:**

```python
# Paso 1-2: Datos del trader
notional_trader = 5 * 95000 = $475,000
leverage_trader = 10.0  # Obtenido de Hyperliquid API

# Paso 3: Calcular MARGEN usado por el trader
margin_trader = 475000 / 10 = $47,500

# Paso 4: Equity del trader
equity_trader = $3,000,000

# Paso 5: Calcular % de riesgo basado en MARGEN
risk_frac = 47500 / 3000000 = 0.0158  # 1.58%

# Paso 6: Aplicar MISMO % a la simulación (SIN leverage)
equity_sim_actual = $10,000
notional_sim = 0.0158 * 10000 = $158.00  # Sin leverage
size_sim = 158.00 / 95000 = 0.00166 BTC

# Crear posición (sin leverage)
position = SimulatedPosition(
    symbol="BTC",
    side="long",
    size_sim=0.00166,
    avg_entry_price_sim=95000.0
)
```

**Verificación:**
- Trader arriesga 1.58% de su equity ($47.5k de $3M) con leverage 10x
- Simulación arriesga 1.58% de su equity ($158 de $10k) sin leverage
- **Mismo % de riesgo, pero sin usar apalancamiento** ✅

**Más tarde, BTC sube a $96,500:**

```python
# Unrealized PnL (size_sim * price movement)
unrealized_pnl = 0.00166 * (96500 - 95000) = $2.49

# Equity actual
equity_sim_actual = 10000 + 2.49 = $10,002.49
```

**Si el trader cierra 2 BTC (40% de su posición) @ $96,500:**

```python
# Proporción cerrada
close_frac = 2 / 5 = 0.4  # 40% de la posición

# En simulación (40% del size simulado)
close_size_sim = 0.4 * 0.00166 = 0.000664 BTC

# Realized PnL
realized_pnl = 0.000664 * (96500 - 95000) = $0.996 ≈ $1.00

# Actualizar posición (60% restante)
new_size_sim = 0.00166 - 0.000664 = 0.001 BTC
position.size_sim = 0.001

# Equity
realized_pnl_sim = $1.00
unrealized_pnl_sim = 0.001 * (96500 - 95000) = $1.50
pnl_total_sim = $2.50
equity_sim_actual = $10,002.50
```

**Nota sobre PnL:**
Los PnLs son proporcionales al riesgo tomado. El trader con 10x leverage tiene:
- 5 BTC × $1,500 = $7,500 de PnL en su cuenta

La simulación sin leverage tiene:
- 0.00166 BTC × $1,500 = $2.49 de PnL

Ratio: $2.49 / $7,500 = 0.033% → correcto porque $10k / $3M = 0.033%

---

## ⚠️ Limitaciones Actuales

**NO incluye:**
- ❌ Fees de trading
- ❌ Funding payments
- ❌ Slippage
- ❌ Liquidaciones

**Futura implementación:**
Estos se añadirán después como módulos opcionales.

---

## 🛠️ Arquitectura del Código

### simulator_engine.py

**Clases principales:**

1. `SimulatedPosition`
   - Representa una posición simulada
   - Calcula unrealized PnL

2. `WalletSimulation`
   - Estado de una simulación de wallet
   - Mantiene posiciones, PnL, equity
   - Método `get_snapshot()` para estado actual

3. `SimulatorEngine`
   - Gestor principal
   - Mantiene múltiples `WalletSimulation`
   - Background loop para actualizar en tiempo real
   - Métodos:
     - `start_simulation(wallet)`
     - `stop_simulation(wallet)`
     - `process_fill(wallet, fill)` - Lógica de copiado proporcional
     - `update_mark_prices()` - Actualiza precios
     - `check_for_new_fills()` - Consulta fills del trader

### api_simulator.py

FastAPI endpoints limpios:
- `POST /sim/start`
- `POST /sim/stop`
- `GET /sim/snapshot`
- `GET /sim/wallets`

---

## 🧪 Testing

### Test Manual

```bash
# 1. Iniciar backend
./start_simulator.sh

# 2. En otra terminal, iniciar simulación
curl -X POST http://localhost:8000/sim/start \
  -H "Content-Type: application/json" \
  -d '{"wallet": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"}'

# 3. Esperar unos segundos (para que procese fills)

# 4. Ver snapshot
curl "http://localhost:8000/sim/snapshot?wallet=0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"

# 5. Ver todas las wallets
curl http://localhost:8000/sim/wallets

# 6. Detener simulación
curl -X POST http://localhost:8000/sim/stop \
  -H "Content-Type: application/json" \
  -d '{"wallet": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"}'
```

---

## 📝 Notas Importantes

1. **Solo datos reales**: El sistema NUNCA genera datos sintéticos. Todo viene de Hyperliquid API.

2. **Timestamp filtering**: Solo se procesan fills con `timestamp >= start_time`. Nunca se simula histórico.

3. **Proporcional**: La clave es copiar el mismo % de riesgo, no el mismo tamaño absoluto.

4. **Sin fees**: Esta versión no resta fees ni funding. Se añadirán después como módulo opcional.

5. **Rate limiting**: El background loop corre cada 5 segundos para evitar rate limits de Hyperliquid API.

6. **Ultra Copy Trading intacto**: Este nuevo backend NO toca el sistema de Ultra Copy Trading. Son completamente independientes.

---

## 🎯 Próximos Pasos

- [ ] Añadir fees de trading (maker/taker)
- [ ] Añadir funding payments
- [ ] Añadir slippage simulation
- [ ] WebSocket en vez de polling para fills
- [ ] Frontend React para visualización
- [ ] Persistencia en BD para histórico
- [ ] Exportar resultados a CSV/JSON

---

**Listo para usar!** 🚀

```bash
cd hyperliquid-copytrade/backend
./start_simulator.sh
```
