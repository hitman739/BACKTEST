# ⚡ Ultra-Low Latency Copy Trading System

Sistema de copy trading optimizado para **latencia mínima** en Hyperliquid.

**Objetivo: Evento → Orden < 100ms**

---

## 🎯 Características Clave

### ⚡ Latencia Mínima
- **WebSocket directo** (no REST polling)
- **Procesamiento asíncrono** (no bloqueos)
- **Estado en memoria** (no base de datos)
- **Fire-and-forget orders** (no espera)

### 📊 Pipeline Optimizado

```
Trader abre posición
    ↓ WebSocket event (~10ms)
Event processor detecta
    ↓ Parsing (~5ms)
Calcula tamaño proporcional
    ↓ Math (~10ms)
Envía orden al exchange
    ↓ API call (~40ms)
Orden ejecutada
    ↓ Confirmación (~20ms)

TOTAL: ~85ms
```

### 🔥 Optimizaciones Implementadas

1. **WebSocket puro** - Sin polling, eventos en tiempo real
2. **Async/await** - No bloqueos en el event loop
3. **In-memory state** - Sin I/O de disco en critical path
4. **Minimal logging** - Solo métricas esenciales durante trading
5. **Direct order submission** - Sin validaciones excesivas
6. **Fire-and-forget** - No espera confirmación para siguiente evento

---

## 🏗️ Arquitectura

### Componentes

#### 1. **UltraLowLatencyWebSocket** (`ultra_websocket.py`)
- Maneja conexión WebSocket con Hyperliquid
- Subscribe a eventos del trader target
- Callback inmediato (no queue)
- Async task creation para no bloquear

#### 2. **UltraOrderExecutor** (`ultra_executor.py`)
- Ejecuta órdenes con mínima latencia
- Market orders con slippage tolerance
- Limit orders si necesario
- Tracking de latencia por orden

#### 3. **UltraCopyTrader** (`ultra_copytrader.py`)
- Manager principal del copy trading
- Sincroniza estado inicial (REST una vez)
- Procesa eventos en tiempo real (WebSocket)
- Calcula y ejecuta órdenes proporcionalmente

#### 4. **API** (`api_ultra.py`)
- REST API simple para control
- Start/Stop/Status endpoints
- Métricas de latencia en tiempo real

---

## 🚀 Quick Start

### 1. Iniciar el backend

```bash
cd /home/user/BACKTEST/hyperliquid-copytrade/backend
./start_ultra.sh
```

### 2. Iniciar copy trading

```bash
curl -X POST http://localhost:8000/start \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "target_wallet": "0x...",
    "copy_ratio": 1.0,
    "testnet": false
  }'
```

### 3. Ver status

```bash
curl http://localhost:8000/status
```

### 4. Parar

```bash
curl -X POST http://localhost:8000/stop
```

---

## 📊 Parámetros

### Copy Ratio

El `copy_ratio` determina qué porcentaje de las posiciones del trader copias:

- **1.0** = Copias 100% (mismo riesgo/reward)
- **0.5** = Copias 50% (mitad del riesgo)
- **2.0** = Copias 200% (doble riesgo) ⚠️

**Cálculo:**
```
my_size = target_size × (my_account / target_account) × copy_ratio
```

**Ejemplo:**
- Target tiene $10,000, abre posición de 1 BTC
- Yo tengo $5,000, copy_ratio = 1.0
- Mi posición = 1 × (5000/10000) × 1.0 = 0.5 BTC

---

## 📈 Métricas de Latencia

El sistema trackea automáticamente:

- **Trades Copied**: Número de órdenes ejecutadas
- **Average Latency**: Promedio evento → orden
- **Min Latency**: Mejor tiempo
- **Max Latency**: Peor tiempo

Ejemplo de output:
```
🚀 COPIED: BTC BUY 0.1 | Latency: 87.3ms (avg: 92.1ms)
🛑 CLOSED: ETH 0.5 | Latency: 65.2ms (avg: 89.4ms)

📊 Copy Trading Stats:
   Trades copied: 15
   Avg latency: 89.4ms
   Min latency: 65.2ms
   Max latency: 142.7ms
```

---

## ⚠️ Consideraciones de Latencia

### Factores que afectan latencia:

1. **Conexión a internet** (30-50ms)
   - Usar VPS cerca de servidores de Hyperliquid
   - Conexión dedicada (no compartida)

2. **Procesamiento local** (10-20ms)
   - CPU rápida
   - Suficiente RAM
   - Sin procesos competidores

3. **API de Hyperliquid** (20-40ms)
   - Varía según carga del exchange
   - Horarios de alto volumen = mayor latencia

### Target realista:

- **Excelente**: < 100ms
- **Bueno**: 100-200ms
- **Aceptable**: 200-500ms
- **Lento**: > 500ms

---

## 🔧 Optimizaciones Avanzadas

### 1. Usar VPS

Para latencia < 50ms, usa un VPS:

**Providers recomendados:**
- AWS EC2 (us-east-1)
- DigitalOcean (New York)
- Vultr (New Jersey)

**Specs mínimas:**
- 2 CPU cores
- 2GB RAM
- 10GB SSD

### 2. Optimizar Python

```bash
# Usar PyPy en lugar de CPython (2-3x más rápido)
pypy3 -m pip install -r requirements.txt
pypy3 api_ultra.py
```

### 3. Prioridad de proceso

```bash
# Dar máxima prioridad al proceso
sudo nice -n -20 python api_ultra.py
```

### 4. Network optimization

```bash
# Aumentar buffer sizes
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
```

---

## 🐛 Troubleshooting

### Latencia Alta (> 500ms)

**Posibles causas:**

1. **Internet lento**
   ```bash
   # Test latency to Hyperliquid
   ping api.hyperliquid.xyz
   ```

2. **CPU sobrecargado**
   ```bash
   # Check CPU usage
   top
   ```

3. **Too many processes**
   - Cierra otros programas
   - No correr en shared hosting

### Órdenes no se ejecutan

**Check:**

1. **API keys correctas**
   - Verifica en Hyperliquid dashboard
   - Permisos de trading habilitados

2. **Balance suficiente**
   - Necesitas margen disponible
   - Check `my_account_value` en status

3. **Tamaño mínimo**
   - Hyperliquid mínimo: 0.001
   - Si muy pequeño, no se ejecuta

### WebSocket desconecta

**Solución:**

- Reconexión automática (built-in)
- Si persiste, check firewall
- Usar puerto 443 si problemas con 80

---

## 📊 Comparación vs Sistemas Tradicionales

| Feature | Sistema Tradicional | Ultra System |
|---------|-------------------|--------------|
| **Método** | REST polling (5-15s) | WebSocket real-time |
| **Latencia** | 5000-15000ms | 50-150ms |
| **CPU** | Alto (polling constante) | Bajo (event-driven) |
| **Precisión** | Puede perder trades | Todos los trades |
| **Escalabilidad** | 1-5 traders | 10+ traders |
| **Overhead** | Database I/O | Solo memoria |

---

## 🔐 Seguridad

### API Keys

**NUNCA:**
- ❌ Commitear API keys en git
- ❌ Compartir API keys
- ❌ Usar keys con permisos de withdrawal

**SIEMPRE:**
- ✅ Usar variables de entorno
- ✅ Permisos mínimos (solo trading)
- ✅ Rotar keys regularmente

### Ejemplo con env vars:

```bash
# .env file
HYPERLIQUID_API_KEY=your_key_here
HYPERLIQUID_API_SECRET=your_secret_here

# Load in script
export $(cat .env | xargs)

# Use in API call
curl -X POST http://localhost:8000/start \
  -H "Content-Type: application/json" \
  -d "{
    \"api_key\": \"$HYPERLIQUID_API_KEY\",
    \"api_secret\": \"$HYPERLIQUID_API_SECRET\",
    \"target_wallet\": \"0x...\",
    \"copy_ratio\": 1.0
  }"
```

---

## 📝 Logs

### Eventos importantes:

```
✅ - Operación exitosa
⚠️ - Warning (no crítico)
❌ - Error (requiere atención)
🚀 - Trade copiado
🛑 - Posición cerrada
📊 - Estadísticas
```

### Ejemplo de log:

```
2025-01-17 12:00:00 - ultra_copytrader - [INFO] - 🚀 Starting ultra-low latency copy trading...
2025-01-17 12:00:01 - ultra_copytrader - [INFO] - 📊 Syncing initial state...
2025-01-17 12:00:02 - ultra_copytrader - [INFO] -    Target account value: $50,000.00
2025-01-17 12:00:02 - ultra_copytrader - [INFO] -    Target positions: 3
2025-01-17 12:00:02 - ultra_copytrader - [INFO] -    My account value: $10,000.00
2025-01-17 12:00:02 - ultra_copytrader - [INFO] - ✅ Initial sync complete
2025-01-17 12:00:02 - ultra_copytrader - [INFO] - ✅ Copy trading active - listening for events
2025-01-17 12:01:15 - ultra_executor - [INFO] - ✅ Order executed: BTC BUY 0.1 (87.3ms)
2025-01-17 12:01:15 - ultra_copytrader - [INFO] - 🚀 COPIED: BTC BUY 0.1000 | Latency: 92.1ms (avg: 92.1ms)
```

---

## 🎓 Conceptos Clave

### Event-Driven Architecture

En lugar de hacer polling constante (REST API cada X segundos), el sistema **espera eventos**:

```python
# ❌ Polling (lento, ineficiente)
while True:
    positions = get_positions()  # REST call
    check_for_changes(positions)
    time.sleep(5)  # 5 segundos de retraso

# ✅ Event-driven (rápido, eficiente)
websocket.subscribe("fills", on_fill_event)

def on_fill_event(event):
    # Ejecuta inmediatamente (< 100ms)
    process_and_copy(event)
```

### Non-Blocking Async

Todo el código usa `async/await` para no bloquear:

```python
# ❌ Blocking (espera respuesta)
result = execute_order()  # Bloquea por 50ms
process_next_event()  # Espera a que termine

# ✅ Non-blocking (continúa inmediatamente)
asyncio.create_task(execute_order())  # No espera
process_next_event()  # Continúa inmediatamente
```

### In-Memory State

Estado se guarda en RAM (no disco) para velocidad:

```python
# ❌ Database (lento)
db.save_position(position)  # I/O disk (~10ms)

# ✅ In-memory (rápido)
self.positions[coin] = position  # RAM (~0.001ms)
```

---

## 🚀 Próximos Pasos

1. **Test con testnet** primero
2. **Monitorear latencia** (debe ser < 150ms)
3. **Ajustar copy_ratio** según tu riesgo
4. **Usar VPS** para mejor latencia
5. **Monitorear 24/7** con alertas

---

## 📞 Soporte

Si tienes problemas:

1. Check logs en la terminal
2. Verifica `/status` endpoint
3. Test conexión a Hyperliquid
4. Revisa API keys

---

**¡Listo para copiar trades con latencia sub-100ms! 🚀**
