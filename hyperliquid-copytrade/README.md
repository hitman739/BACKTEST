# Hyperliquid Copy Trading

Sistema de copy trading para Hyperliquid con dos módulos:

- 📊 **Simulator** - Simulación proporcional (mismo leverage que el trader, sin dinero real)
- ⚡ **Ultra Copy Trading** - Copy trading REAL en Hyperliquid

---

## 🚀 Inicio Rápido

### Simulator

```bash
cd backend
python3 api_simulator.py
```

**Endpoints:**
- `POST /sim/start` - Iniciar simulación (resetea estado, empieza desde NOW)
- `GET /sim/snapshot?wallet=...` - Ver estado actual
- `GET /sim/debug/{wallet}` - Debug info (últimos 5 fills, equity, PnL)
- `GET /docs` - Documentación interactiva

**Puerto:** 8000

### Ultra Copy Trading

```bash
cd backend
python3 api_new.py
```

**Endpoints:**
- `POST /wallet/add` - Agregar wallet
- `GET /status` - Ver wallets activas
- WebSocket: `ws://localhost:8000/ws`

**Puerto:** 8000

### Frontend

```bash
cd frontend
npm install  # Solo la primera vez
npm run dev
```

**Puerto:** 5173

**Rutas disponibles:**
- `/` - Home
- `/simulator` - Simulator (usa api_new.py)
- `/simulator-v2` - Simulator V2 con WebSockets
- `/copytrading` - Ultra Copy Trading

---

## 📁 Estructura

```
hyperliquid-copytrade/
├── backend/              # Backend Python (FastAPI)
│   ├── api_simulator.py  # Simulator (lógica proporcional con leverage)
│   ├── api_new.py        # Ultra Copy Trading + legacy endpoints
│   ├── simulator_engine.py
│   ├── indexer.py
│   ├── database.py
│   └── requirements.txt
├── frontend/             # React + Vite
│   ├── src/
│   │   ├── Simulator.jsx
│   │   ├── SimulatorV2.jsx
│   │   └── UltraCopyTrading.jsx
│   └── package.json
├── scripts/              # Scripts de inicio/parada
│   ├── start_simulator.sh
│   ├── stop_simulator.sh
│   └── CLEAN_AND_PULL.sh
├── docs/                 # Documentación
│   ├── INSTRUCCIONES.md
│   ├── README_SIMULATOR.md
│   └── PULL_COMMANDS.md
└── README.md            # Este archivo
```

---

## 📊 Simulator - Lógica Proporcional

El simulator copia al trader de forma proporcional usando el **mismo leverage**:

```
1. trader_notional = trader_size * price
2. trader_margin = trader_notional / trader_leverage
3. risk_fraction = trader_margin / trader_equity
4. my_notional = risk_fraction * my_equity * trader_leverage  # MISMO leverage
5. my_size = my_notional / price
```

### Características importantes:
- ✅ Resetea estado al agregar wallet (empieza con $10,000)
- ✅ Solo procesa fills DESDE NOW (no histórico)
- ✅ Usa el mismo leverage que el trader
- ✅ Logging detallado por trade
- ✅ Endpoint `/sim/debug/{wallet}` para troubleshooting

---

## 🛠️ Instalación

### Dependencias Backend

```bash
cd backend
pip3 install -r requirements.txt
```

### Dependencias Frontend

```bash
cd frontend
npm install
```

---

## 🔧 Scripts Disponibles

Todos en la carpeta `scripts/`:

```bash
# Iniciar simulator
./scripts/start_simulator.sh

# Detener servicios
./scripts/stop_simulator.sh

# Limpiar repo y hacer git pull
./scripts/CLEAN_AND_PULL.sh
```

---

## 📚 Documentación

- **[Instrucciones Completas](docs/INSTRUCCIONES.md)** - Guía paso a paso para usar el simulator
- **[README Simulator](docs/README_SIMULATOR.md)** - Documentación técnica del simulator
- **[Pull Commands](docs/PULL_COMMANDS.md)** - Cómo actualizar el repo sin errores

---

## 🔍 Troubleshooting

### Puerto 8000 en uso

```bash
lsof -i:8000
kill -9 <PID>
```

### Error al hacer git pull

```bash
./scripts/CLEAN_AND_PULL.sh
```

O manualmente:
```bash
git stash
git clean -f -d
git pull origin claude/fix-copytrading-simulator-016Rwzzxe4AenGmWU5Qw3sqH
```

### Ver logs del simulator

Los logs aparecen en la terminal donde corriste `python3 api_simulator.py`. Verás:

```
================================================================================
🔄 NEW FILL from trader 0x9b55c...
   Coin: BTC | Side: B | Trader Size: 0.500000 | Price: $50000.00
   Trader Leverage: 10.0x
   ...
📊 SIMULATED FILL:
   My Size: 0.050000 BTC
   My Leverage: 10.0x (same as trader)
   ...
✅ OPENED LONG position: 0.050000 BTC @ $50000.00
================================================================================
```

---

## 📝 Notas

1. **Simulator** y **Ultra Copy Trading** son backends **separados** que corren en puerto 8000
2. No corras ambos backends al mismo tiempo (puerto compartido)
3. El frontend puede conectarse a cualquiera de los dos backends
4. `api_new.py` incluye endpoints legacy para compatibilidad con Simulator.jsx

---

## 🆘 Ayuda

Si tienes problemas:
1. Revisa los logs en la terminal del backend
2. Usa el endpoint `/sim/debug/{wallet}` para ver qué está pasando
3. Consulta la documentación en `docs/`
4. Verifica que solo un backend esté corriendo en puerto 8000
