# 🚀 CÓMO ACTIVAR EL SIMULADOR DE COPY TRADING

## ⚡ MÉTODO RÁPIDO (UN SOLO COMANDO)

Desde el directorio `hyperliquid-copytrade/`:

```bash
./start_simulator.sh
```

Este script automáticamente:
- ✅ Arranca el backend (api_new.py) en puerto 8000
- ✅ Arranca el frontend (Vite) en puerto 5173
- ✅ Instala dependencias si es necesario
- ✅ Verifica que todo esté funcionando

---

## 📝 MÉTODO MANUAL (PASO A PASO)

### PASO 1: Arrancar el Backend

```bash
cd hyperliquid-copytrade/backend

# Instalar dependencias (solo la primera vez)
pip3 install -r requirements.txt

# Arrancar backend
python3 api_new.py
```

✅ **Verificar que funciona:**
```bash
curl http://localhost:8000/health
# Debería responder: {"status":"healthy"}
```

---

### PASO 2: Arrancar el Frontend

Abre una **nueva terminal** y ejecuta:

```bash
cd hyperliquid-copytrade/frontend

# Instalar dependencias (solo la primera vez)
npm install

# Arrancar frontend
npm run dev
```

✅ **El frontend arrancará en:** http://localhost:5173

---

## 🌐 USAR EL SIMULADOR

1. **Abre tu navegador** en: http://localhost:5173

2. **Selecciona el simulador que quieres usar:**
   - **Simulator** (ruta: `/simulator`)
   - **Simulator V2** (ruta: `/simulator-v2`) - Con WebSockets en tiempo real

3. **Agrega una wallet** para simular:
   - Pega la dirección de la wallet (ej: `0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b`)
   - Define el balance inicial (default: 10,000 USDT)
   - Haz clic en **"Add Wallet"**

4. **El simulador empezará a trackear:**
   - Fills del trader
   - Posiciones abiertas
   - PnL en tiempo real
   - ROI y estadísticas

---

## 🛑 DETENER LOS SERVICIOS

```bash
# Detener backend
pkill -f 'python3 api_new'

# Detener frontend
pkill -f 'vite'
```

O simplemente presiona **Ctrl+C** en cada terminal.

---

## 📋 VER LOGS

Si algo no funciona, revisa los logs:

```bash
# Logs del backend
tail -f /tmp/api_new.log

# Logs del frontend (si usaste el script)
tail -f /tmp/vite.log
```

---

## 🔧 TROUBLESHOOTING

### ❌ Error: "Address already in use"

**Problema:** Ya hay algo corriendo en el puerto 8000 o 5173

**Solución:**
```bash
# Ver qué está usando el puerto
lsof -i:8000
lsof -i:5173

# Matar el proceso
kill -9 <PID>
```

### ❌ Frontend muestra "Failed to fetch" o "Network Error"

**Problema:** El backend no está corriendo

**Solución:**
```bash
# Verificar que el backend esté activo
curl http://localhost:8000/health

# Si no responde, arranca el backend
cd hyperliquid-copytrade/backend && python3 api_new.py
```

### ❌ "Not Found" al agregar wallet

**Problema:** Estás usando el frontend incorrecto con el backend

**Solución:** El backend `api_new.py` ahora soporta ambos frontends. Asegúrate de que esté corriendo la versión actualizada.

```bash
cd hyperliquid-copytrade/backend
git pull
python3 api_new.py
```

---

## 📊 ENDPOINTS DISPONIBLES

### Backend API (http://localhost:8000)

**Documentación interactiva:** http://localhost:8000/docs

**Endpoints principales:**
- `GET /health` - Health check
- `GET /status` - Estado de wallets trackeadas
- `POST /wallet/add` - Agregar wallet (formato nuevo)
- `POST /add-wallet` - Agregar wallet (formato legacy)
- `DELETE /wallet/{address}` - Remover wallet
- `DELETE /remove-wallet/{address}` - Remover wallet (legacy)
- `WS /ws` - WebSocket para updates en tiempo real

---

## ⚙️ CONFIGURACIÓN

### Backend (api_new.py)

El backend usa:
- **Database:** SQLite local (`hyperliquid_data.db`)
- **Indexer:** Sincroniza datos de Hyperliquid en background
- **Metrics Calculator:** Calcula PnL, fees, ROI cada 60 segundos
- **WebSocket:** Actualiza frontend cada segundo

### Frontend

El frontend usa:
- **Vite** para desarrollo rápido
- **React** para la UI
- **WebSocket** para updates en tiempo real (SimulatorV2)
- **Polling** cada 5 segundos (Simulator)

---

## 🎯 DIFERENCIAS ENTRE SIMULADORES

### Simulator (`/simulator`)
- Endpoints legacy: `/add-wallet`, `/remove-wallet`
- Actualización por polling cada 5 segundos
- Más simple

### Simulator V2 (`/simulator-v2`)
- Endpoints nuevos: `/wallet/add`, `/wallet/{address}`
- WebSocket para updates en tiempo real (cada 1 segundo)
- Fee Factor badges
- UI mejorada

**Ambos funcionan con el mismo backend `api_new.py`**

---

## 📞 SOPORTE

Si tienes problemas:

1. Revisa los logs del backend: `tail -f /tmp/api_new.log`
2. Revisa los logs del frontend: `tail -f /tmp/vite.log`
3. Verifica que ambos servicios estén corriendo:
   ```bash
   lsof -i:8000  # Backend
   lsof -i:5173  # Frontend
   ```
4. Reinicia todo con el script: `./start_simulator.sh`
