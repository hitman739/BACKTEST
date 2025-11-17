# Hyperliquid CopyTrade API v2

## 🚀 Nueva Arquitectura

Esta versión utiliza WebSocket + Base de datos local para eliminar completamente el problema de rate limiting y proporcionar actualizaciones en tiempo real.

### Diferencias con v1:

| Aspecto | v1 (Antigua) | v2 (Nueva) |
|---------|-------------|------------|
| **Datos** | Polling REST API cada 5-15s | WebSocket real-time |
| **Almacenamiento** | En memoria | SQLite local |
| **Rate Limiting** | ❌ Problema constante | ✅ Sin problemas |
| **Velocidad** | Polling interval | ⚡ Instantáneo |
| **Historial** | REST cada vez | ✅ BD local |
| **Actualizaciones Frontend** | Manual refresh | 🔥 WebSocket cada 1s |

---

## 📊 Componentes

### 1. **Database** (`database.py`)
- SQLite para almacenamiento local
- Tablas: `wallets`, `fills`, `positions`, `orders`, `funding_payments`, `wallet_metrics`
- Indexado para queries rápidas
- Puede migrar a PostgreSQL fácilmente

### 2. **Indexer** (`indexer.py`)
- Se conecta al WebSocket de Hyperliquid
- Recibe datos en tiempo real:
  - `userEvents`: fills, orders, positions
  - `userFills`: trades ejecutados
  - `userFundings`: pagos de funding
- Sync inicial vía REST (solo una vez)
- Guarda todo en la BD local

### 3. **Metrics Calculator** (`metrics_calculator.py`)
- Calcula métricas cada 60 segundos:
  - Equity
  - Total PnL (realized + unrealized)
  - Volume
  - Fees
  - **Fee Factor** (profit_after_fees / profit_before_fees)
  - ROI
- Lee de BD local (NO toca Hyperliquid API)

### 4. **API** (`api_new.py`)
- FastAPI con endpoints:
  - `POST /wallet/add` - Añadir wallet
  - `DELETE /wallet/{address}` - Remover wallet
  - `GET /wallet/{address}/summary` - Resumen completo
  - `GET /wallet/{address}/fills` - Historial de trades
  - `GET /wallet/{address}/positions` - Posiciones abiertas
  - `GET /wallet/{address}/equity` - Historial de equity
  - `GET /wallet/{address}/fees` - Estadísticas de fees
  - `GET /status` - Estado global
  - `WS /ws` - WebSocket para actualizaciones cada 1s

---

## 🔥 Fee Factor

El **Fee Factor** mide cuánto del profit se retiene después de pagar fees:

```
fee_factor = (profit_after_fees) / (profit_before_fees)
```

**Ejemplo:**
- Profit antes de fees: $1000
- Fees estimadas: $200
- Profit después de fees: $800
- Fee Factor: 0.80 (80%)

**Dos versiones:**
1. **Fee Factor Mixed** (75% maker + 25% taker) - Escenario realista
2. **Fee Factor Taker** (100% taker) - Peor caso

**Interpretación:**
- `1.0` = Sin impacto de fees (imposible)
- `0.8` = Retiene 80% del profit (bueno)
- `0.5` = Pierde 50% en fees (malo)
- `< 0` = Fees superan el profit (terrible)

---

## 🎯 Flujo de Datos

```
Hyperliquid (WebSocket)
    ↓ real-time
Indexer
    ↓ guarda
Database (SQLite)
    ↓ lee
Metrics Calculator
    ↓ calcula cada 60s
Database (wallet_metrics)
    ↓ lee
API
    ↓ broadcast cada 1s via WebSocket
Frontend
```

---

## 🚀 Uso

### Iniciar el backend:

```bash
cd /home/user/BACKTEST/hyperliquid-copytrade/backend
./start_v2.sh
```

### Añadir una wallet:

```bash
curl -X POST http://localhost:8000/wallet/add \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0x...",
    "initial_balance": 10000.0
  }'
```

### Obtener resumen:

```bash
curl http://localhost:8000/wallet/0x.../summary
```

### WebSocket (JavaScript):

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'metrics_update') {
    // Actualizar UI cada segundo
    console.log(data.data);
  }
};
```

---

## 📈 Performance

- **Sin rate limiting**: WebSocket no tiene límites como REST
- **Actualizaciones instantáneas**: No esperas 5-15 segundos
- **Queries rápidas**: BD local = microsegundos vs API = segundos
- **Escalable**: Puedes trackear 100+ wallets sin problemas
- **Eficiente**: Una conexión WebSocket para todas las wallets

---

## 🔧 Configuración

### Cambiar a PostgreSQL:

Edita `database.py` y cambia:

```python
self.conn = sqlite3.connect(...)
```

Por:

```python
import psycopg2
self.conn = psycopg2.connect(
    dbname="hyperliquid",
    user="...",
    password="...",
    host="localhost"
)
```

### Cambiar intervalo de métricas:

En `api_new.py`:

```python
asyncio.create_task(
    metrics_calculator.start_periodic_updates(
        interval_seconds=30  # Cambiar de 60 a 30
    )
)
```

### Cambiar intervalo de broadcast:

En `broadcast_updates()`:

```python
await asyncio.sleep(0.5)  # Cambiar de 1s a 0.5s
```

---

## 🎮 Endpoints de la API

### Wallets

- `POST /wallet/add` - Añadir wallet para trackear
- `DELETE /wallet/{address}` - Remover wallet
- `GET /wallet/{address}/summary` - Resumen completo con métricas
- `GET /wallet/{address}/fills?limit=100` - Historial de trades
- `GET /wallet/{address}/positions` - Posiciones abiertas
- `GET /wallet/{address}/equity?limit=100` - Historial de equity
- `GET /wallet/{address}/fees` - Estadísticas de fees y fee factor

### Sistema

- `GET /status` - Estado de todas las wallets
- `GET /health` - Health check
- `WS /ws` - WebSocket para updates en tiempo real

---

## 🐛 Debugging

### Ver logs del indexer:

```bash
tail -f hyperliquid_indexer.log
```

### Ver contenido de la BD:

```bash
sqlite3 hyperliquid_data.db

# Ver wallets
SELECT * FROM wallets;

# Ver últimos fills
SELECT * FROM fills ORDER BY time DESC LIMIT 10;

# Ver métricas
SELECT * FROM wallet_metrics ORDER BY timestamp DESC LIMIT 10;
```

### Test manual:

```python
from database import Database
from metrics_calculator import MetricsCalculator

db = Database()
calc = MetricsCalculator(db)

# Calcular métricas para una wallet
metrics = calc.calculate_metrics("0x...")
print(metrics)
```

---

## ✅ Ventajas de v2

1. ✅ **Sin rate limiting** - WebSocket no tiene límites
2. ✅ **Tiempo real** - Actualizaciones instantáneas
3. ✅ **Escalable** - 100+ wallets sin problemas
4. ✅ **Rápido** - Queries en microsegundos
5. ✅ **Histórico completo** - Todo guardado localmente
6. ✅ **Fee Factor** - Métrica clave para evaluar traders
7. ✅ **WebSocket al frontend** - Updates cada 1 segundo
8. ✅ **Profesional** - Arquitectura similar a HyperSignals

---

## 📝 TODO

- [ ] Migrar frontend a usar WebSocket
- [ ] Añadir endpoint de copy trading
- [ ] Añadir simulador con BD local
- [ ] Dashboard con gráficos de equity
- [ ] Alertas cuando un trader abre/cierra posición
