# 🚀 Comandos para ejecutar en tu Mac

## Arrancar el Backend Unificado (Simulator + Ultra)

### Opción 1: Desde la carpeta del backend (Recomendado)

```bash
cd hyperliquid-copytrade/backend
./start.sh --reload
```

### Opción 2: Desde la raíz del proyecto

```bash
cd hyperliquid-copytrade
backend/start.sh --reload
```

### Opción 3: Sin auto-reload (Producción)

```bash
cd hyperliquid-copytrade/backend
./start.sh
```

### Opción 4: Puerto personalizado

```bash
cd hyperliquid-copytrade/backend
./start.sh --port 8080 --reload
```

## ✅ Qué hace el script automáticamente

Cuando ejecutas `./start.sh --reload`, el script:

1. ✅ Crea el virtual environment de Python (si no existe)
2. ✅ Activa el virtual environment
3. ✅ Instala/actualiza pip
4. ✅ Instala todas las dependencias de `requirements.txt`
5. ✅ Crea el archivo `.env` desde `.env.example` (si no existe)
6. ✅ Inicializa la base de datos SQLite
7. ✅ Arranca el servidor con AMBOS módulos (Simulator + Ultra)

**NO necesitas hacer NADA manualmente** - solo ejecuta el script.

## 📊 Verificar que todo funciona

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "modules": {
    "simulator": "active",
    "ultra": "active"
  }
}
```

### 2. Ver información de los módulos

```bash
curl http://localhost:8000/
```

### 3. Abrir documentación interactiva

En tu navegador:
```
http://localhost:8000/docs
```

## 🎮 Probar el Simulator

### 1. Registrarse

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test1234"}'
```

Guarda el `access_token` que te devuelve.

### 2. Crear configuración de simulador

```bash
curl -X POST http://localhost:8000/api/simulator/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "target_trader": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b",
    "initial_balance": 10000,
    "leverage": 5
  }'
```

### 3. Simular un trade

```bash
curl -X POST http://localhost:8000/api/simulator/trade \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "config_id": "CONFIG_ID_DEL_PASO_ANTERIOR",
    "symbol": "BTC",
    "side": "LONG",
    "size": 0.1,
    "price": 50000
  }'
```

## ⚡ Probar Ultra Copy Trading

### 1. Conectar wallet de Hyperliquid

```bash
curl -X POST http://localhost:8000/api/account/set-wallet \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{"wallet_address": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"}'
```

### 2. Crear configuración de copy trading

```bash
curl -X POST http://localhost:8000/api/ultra/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "target_trader": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b",
    "margin_multiplier": 1.0,
    "testnet_mode": true
  }'
```

### 3. Iniciar monitoreo automático

```bash
curl -X POST http://localhost:8000/api/ultra/config/CONFIG_ID/start \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

## 🛑 Parar el servidor

Simplemente presiona `Ctrl+C` en la terminal donde está corriendo.

## 🐛 Solución de problemas

### Error: "Permission denied: './start.sh'"

```bash
chmod +x hyperliquid-copytrade/backend/start.sh
```

### Error: "Port 8000 already in use"

```bash
# Opción 1: Matar el proceso
lsof -ti:8000 | xargs kill -9

# Opción 2: Usar otro puerto
./start.sh --port 8001 --reload
```

### Error: "python3 command not found"

Instala Python 3:
```bash
brew install python@3.11
```

### Error: "ModuleNotFoundError"

```bash
# Reinstala las dependencias
cd hyperliquid-copytrade/backend
source venv/bin/activate
pip install -r requirements.txt
```

### Limpiar todo y empezar de cero

```bash
cd hyperliquid-copytrade/backend
rm -rf venv
rm copytrade.db
./start.sh --reload
```

## 📖 Documentación completa

Lee el archivo `README.md` para más información:
```bash
cat hyperliquid-copytrade/README.md
```

O abre la documentación interactiva:
```
http://localhost:8000/docs
```

---

## 🎯 Resumen - Solo esto necesitas ejecutar:

```bash
cd hyperliquid-copytrade/backend
./start.sh --reload
```

**¡Eso es todo!** 🚀

El servidor arrancará con:
- ✅ Simulator en `/api/simulator/*`
- ✅ Ultra Copy Trading en `/api/ultra/*`
- ✅ Ambos corriendo simultáneamente
- ✅ Sin necesidad de parar/arrancar entre módulos

Abre http://localhost:8000/docs para ver todos los endpoints disponibles.
