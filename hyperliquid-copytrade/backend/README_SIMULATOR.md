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

### 3. Copiado Proporcional con Leverage

La clave del sistema: **copiar el mismo % de MARGEN usado**, considerando el leverage.

⚠️ **IMPORTANTE**: El leverage multiplica el notional, pero NO el riesgo real. El riesgo real es el **margen usado**.

Cuando el trader abre un trade:

```python
# 1. Calcular notional del trader
notional_trader = abs(size_trader * price_fill)

# 2. Obtener leverage del trader (de Hyperliquid API)
leverage_trader = [leverage de la posición del trader]

# 3. Calcular MARGEN USADO (no notional)
# El margen es el dinero real en riesgo
margin_used_trader = notional_trader / leverage_trader

# 4. Obtener equity del trader
equity_trader = [de Hyperliquid API]

# 5. Calcular % de riesgo basado en MARGEN
risk_frac = margin_used_trader / equity_trader

# 6. Aplicar mismo % de margen a la simulación
margin_sim = risk_frac * equity_sim_actual

# 7. Aplicar el MISMO LEVERAGE que el trader
notional_sim = margin_sim * leverage_trader
size_sim = notional_sim / price_fill
```

**Ejemplo con Leverage:**
- **Trader**:
  - Equity: $3,000,000
  - Abre: 50 BTC @ $100k = $5M notional
  - Leverage: 10x
  - **Margen usado**: $5M / 10 = $500k
  - **Risk %**: $500k / $3M = 16.67%

- **Simulación**:
  - Equity: $10,000
  - Risk %: 16.67% (mismo que el trader)
  - **Margen usado**: $10k * 16.67% = $1,667
  - Leverage: 10x (mismo que el trader)
  - **Notional**: $1,667 * 10 = $16,670
  - Size: $16,670 / $100k = **0.1667 BTC**

**Sin Leverage (1x):**
- Trader: $3M equity, abre $150k → usa 5% de su equity
- Simulación: $10k equity, abre $500 → usa 5% de su equity
- **Mismo riesgo relativo, diferente tamaño absoluto**

### 4. Gestión de Posiciones

Para cada símbolo, la simulación mantiene:
- `size_sim` - Tamaño de la posición simulada
- `avg_entry_price_sim` - Precio medio de entrada
- `leverage` - Leverage usado (copiado del trader)

Acciones:
- **Aumentar posición**: Recalcula `avg_entry_price_sim` como promedio ponderado, actualiza `leverage`
- **Reducir posición**: Calcula `realized_pnl_sim` sobre la parte cerrada
- **Cerrar posición**: `realized_pnl_sim` y limpia posición

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
      "leverage": 5.0,
      "mark_price": 96500.0,
      "unrealized_pnl_pos": 22.50
    },
    {
      "symbol": "ETH",
      "side": "short",
      "size_sim": 2.5,
      "avg_entry_price_sim": 3500.0,
      "leverage": 3.0,
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
- Abre long BTC: 5 BTC @ $95,000
- Notional: $475,000
- **Leverage: 10x**
- **Margen usado**: $475k / 10 = $47,500
- **Risk %**: $47,500 / $3M = 1.58% de su equity

### Simulación

**Estado inicial:**
- `equity_sim_inicial = $10,000`

**Al detectar el fill:**

```python
# Cálculo proporcional CON LEVERAGE
notional_trader = 5 * 95000 = $475,000
leverage_trader = 10.0  # Obtenido de Hyperliquid API
margin_used_trader = 475000 / 10 = $47,500

equity_trader = $3,000,000
risk_frac = 47500 / 3000000 = 0.0158  # 1.58% (basado en MARGEN)

# Aplicar a simulación
equity_sim_actual = $10,000  # (asumiendo que es el primer trade)
margin_sim = 0.0158 * 10000 = $158.33  # Margen en simulación

# Aplicar MISMO leverage que el trader
notional_sim = 158.33 * 10 = $1,583.33
size_sim = 1583.33 / 95000 = 0.01667 BTC

# Crear posición
position = SimulatedPosition(
    symbol="BTC",
    side="long",
    size_sim=0.01667,
    avg_entry_price_sim=95000.0,
    leverage=10.0  # Mismo leverage que el trader
)
```

**Verificación:**
- Trader usa 1.58% de su equity en margen
- Simulación usa 1.58% de su equity en margen ($158.33)
- Ambos con leverage 10x → mismo riesgo relativo ✅

**Más tarde, BTC sube a $96,500:**

```python
# Unrealized PnL
unrealized_pnl = 0.01667 * (96500 - 95000) = $25.00

# Equity actual
equity_sim_actual = 10000 + 25 = $10,025.00
```

**Si el trader cierra 2 BTC @ $96,500:**

```python
# Proporción cerrada
close_frac = 2 / 5 = 0.4  # 40% de la posición

# En simulación
close_size_sim = 0.4 * 0.01667 = 0.00667 BTC

# Realized PnL
realized_pnl = 0.00667 * (96500 - 95000) = $10.00

# Actualizar posición
new_size_sim = 0.01667 - 0.00667 = 0.01 BTC
position.size_sim = 0.01

# Equity
realized_pnl_sim = $10.00
unrealized_pnl_sim = 0.01 * (96500 - 95000) = $15.00
pnl_total_sim = $25.00
equity_sim_actual = $10,025.00
```

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
