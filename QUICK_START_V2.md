# 🚀 Quick Start - Hyperliquid CopyTrade v2

## Nueva Arquitectura: WebSocket + Base de Datos Local

### ¿Qué cambió?

| Antes (v1) | Ahora (v2) |
|------------|-----------|
| ❌ Polling REST API cada 5-15s | ✅ WebSocket real-time |
| ❌ Rate limiting constante | ✅ Sin límites |
| ❌ Datos en memoria | ✅ Base de datos local |
| ❌ Frontend consulta Hyperliquid | ✅ Frontend consulta tu backend |
| ❌ Lento y problemático | ✅ Rápido y profesional |

---

## 📋 Cómo funciona

```
Hyperliquid WebSocket
    ↓ (real-time)
Indexer (guarda todo)
    ↓
Base de Datos Local (SQLite)
    ↓
Metrics Calculator (cada 60s)
    ↓
API (expone endpoints)
    ↓ (WebSocket cada 1s)
Frontend (updates en tiempo real)
```

---

## 🔧 Instalación

### 1. Instalar dependencias

```bash
cd /home/user/BACKTEST/hyperliquid-copytrade/backend

pip install fastapi uvicorn websockets hyperliquid-python-sdk
```

### 2. Probar el sistema

```bash
# Test completo
python test_system.py
```

Esto va a:
- Crear la base de datos
- Conectarse al WebSocket
- Sincronizar historial de una wallet
- Calcular métricas
- Mostrar resultados

---

## 🚀 Iniciar el Backend

```bash
cd /home/user/BACKTEST/hyperliquid-copytrade/backend

./start_v2.sh
```

El servidor correrá en `http://localhost:8000`

---

## 🧪 Probar con cURL

### Añadir una wallet:

```bash
curl -X POST http://localhost:8000/wallet/add \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0x329c787b163a730bd7900df2beb3ff4fe4670375",
    "initial_balance": 10000.0
  }'
```

### Ver resumen:

```bash
curl http://localhost:8000/wallet/0x329c787b163a730bd7900df2beb3ff4fe4670375/summary
```

### Ver trades:

```bash
curl http://localhost:8000/wallet/0x329c787b163a730bd7900df2beb3ff4fe4670375/fills
```

### Ver fee factor:

```bash
curl http://localhost:8000/wallet/0x329c787b163a730bd7900df2beb3ff4fe4670375/fees
```

### Ver estado global:

```bash
curl http://localhost:8000/status
```

---

## 🌐 Frontend

### Opción 1: Usar el nuevo componente

Edita `/home/user/BACKTEST/hyperliquid-copytrade/frontend/src/App.jsx`:

```jsx
import SimulatorV2 from './SimulatorV2'

function App() {
  return <SimulatorV2 />
}
```

### Opción 2: Conectar manualmente

```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws')

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)

  if (data.type === 'metrics_update') {
    console.log('Metrics updated:', data.data)
    // Update UI aquí
  }
}

// Add wallet
await fetch('http://localhost:8000/wallet/add', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    wallet_address: '0x...',
    initial_balance: 10000
  })
})

// Get summary
const summary = await fetch('http://localhost:8000/wallet/0x.../summary')
const data = await summary.json()
console.log(data.metrics)
```

---

## 📊 Endpoints Disponibles

### Wallets
- `POST /wallet/add` - Añadir wallet
- `DELETE /wallet/{address}` - Remover wallet
- `GET /wallet/{address}/summary` - Resumen completo
- `GET /wallet/{address}/fills` - Historial de trades
- `GET /wallet/{address}/positions` - Posiciones abiertas
- `GET /wallet/{address}/equity` - Historial de equity
- `GET /wallet/{address}/fees` - Fee Factor y estadísticas

### Sistema
- `GET /status` - Estado de todas las wallets
- `GET /health` - Health check
- `WS /ws` - WebSocket (updates cada 1s)

---

## 💡 Fee Factor

El **Fee Factor** mide cuánto profit retienes después de fees:

```
fee_factor = (profit_after_fees) / (profit_before_fees)
```

**Ejemplo:**
- Profit: $1000
- Fees: $150
- Fee Factor: 0.85 (85%)

**Dos versiones:**
- **FFr** (mixed): 75% maker + 25% taker = realista
- **FFt** (taker): 100% taker = peor caso

**Interpretación:**
- `0.9+` = Excelente (retiene >90%)
- `0.8+` = Bueno (retiene >80%)
- `0.7+` = Average
- `0.6+` = Malo
- `<0.6` = Terrible

---

## 🐛 Troubleshooting

### El WebSocket no conecta

```bash
# Verifica que el backend esté corriendo
curl http://localhost:8000/health

# Debería responder: {"status":"healthy"}
```

### No ve datos

```bash
# Verifica la base de datos
sqlite3 hyperliquid_data.db

# Ver wallets
SELECT * FROM wallets;

# Ver últimos fills
SELECT * FROM fills ORDER BY time DESC LIMIT 10;

# Ver métricas
SELECT * FROM wallet_metrics ORDER BY timestamp DESC LIMIT 5;
```

### Logs

Los logs se imprimen en la consola donde corriste `./start_v2.sh`

Busca:
- `✅ Wallet ... fully indexed and subscribed` = wallet añadida correctamente
- `🔥 New fill: ...` = trade detectado en tiempo real
- `📡 Subscribed to ...` = WebSocket conectado
- `⚠️ API RATE LIMIT` = (no debería pasar con v2, pero si pasa, revisa)

---

## ✅ Ventajas de v2

1. **Sin rate limiting** - WebSocket no tiene límites como REST
2. **Tiempo real** - Actualizaciones instantáneas, no cada 5-15s
3. **Escalable** - Puedes trackear 100+ wallets sin problemas
4. **Rápido** - Queries en microsegundos (BD local)
5. **Histórico completo** - Todo guardado, no se pierde nada
6. **Fee Factor** - Métrica clave para evaluar traders
7. **Profesional** - Arquitectura similar a HyperSignals

---

## 📝 Próximos Pasos

1. ✅ Backend funcionando con WebSocket
2. ⏳ Integrar frontend con SimulatorV2.jsx
3. ⏳ Añadir copy trading real
4. ⏳ Dashboard con gráficos
5. ⏳ Alertas de trades

---

## 🤝 Comparación

### v1 (viejo):
```python
# Cada 5-15 segundos
while True:
    data = hyperliquid.user_state(wallet)  # ❌ API call
    await asyncio.sleep(5)  # ❌ Rate limit
```

### v2 (nuevo):
```python
# WebSocket (tiempo real)
websocket.subscribe("userEvents", wallet)  # ✅ Una vez

def on_fill(data):
    database.save(data)  # ✅ Instantáneo
```

---

¿Preguntas? Revisa `README_V2.md` para más detalles técnicos.
