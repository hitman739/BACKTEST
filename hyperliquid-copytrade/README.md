# Hyperliquid Copy Trading App - Unified Backend

Sistema completo de copy trading para Hyperliquid con **dos módulos que corren simultáneamente**:
- 🎮 **Simulator**: Simulación segura de copy trading sin dinero real
- ⚡ **Ultra Copy Trading**: Copy trading REAL en Hyperliquid

## 🚀 Características

### Backend Unificado
- **Un solo servidor** que corre ambos módulos simultáneamente
- **Puerto único** (8000) con rutas organizadas por módulo
- **Sin necesidad de parar/arrancar** procesos entre módulos
- **API REST completa** con documentación automática (Swagger)

### Módulo Simulator (`/api/simulator`)
- Simula copy trading sin ejecutar trades reales
- Perfecto para probar estrategias
- Tracking completo de P&L simulado
- Sin riesgo financiero

### Módulo Ultra Copy Trading (`/api/ultra`)
- **Copy trading REAL** en Hyperliquid
- Monitoreo via WebSocket de traders objetivo
- Ejecución automática de trades
- Gestión de posiciones en tiempo real
- ⚠️ **ADVERTENCIA**: Ejecuta trades reales con dinero real

### Autenticación y Seguridad
- Sistema completo de registro/login con JWT
- Gestión de wallets de Hyperliquid
- Validación en tiempo real contra Hyperliquid API
- Encriptación de datos sensibles
- Rutas protegidas con Bearer tokens

## 📋 Requisitos

- Python 3.10+
- Node.js 18+ (para el frontend)
- pip y virtualenv
- Cuenta de Hyperliquid (para Ultra Copy Trading)

## 🛠️ Instalación Rápida

### Backend (Un solo comando)

```bash
cd hyperliquid-copytrade/backend
./start.sh --reload
```

Eso es todo! El script automáticamente:
1. ✅ Crea el virtual environment
2. ✅ Instala todas las dependencias
3. ✅ Inicializa la base de datos
4. ✅ Arranca el servidor con ambos módulos

**El servidor estará disponible en:** `http://localhost:8000`

### Frontend

```bash
cd hyperliquid-copytrade/frontend
npm install
npm run dev
```

**El frontend estará disponible en:** `http://localhost:5173`

## 📖 Uso del Backend Unificado

### Arrancar el servidor

**Modo desarrollo (con auto-reload):**
```bash
cd hyperliquid-copytrade/backend
./start.sh --reload
```

**Modo producción:**
```bash
cd hyperliquid-copytrade/backend
./start.sh
```

**Puerto personalizado:**
```bash
./start.sh --port 8080 --reload
```

### Parar el servidor

Simplemente presiona `Ctrl+C` en la terminal donde está corriendo.

## 🌐 Endpoints Disponibles

### General
- `GET /` - Información de la API y módulos activos
- `GET /health` - Health check
- `GET /docs` - Documentación interactiva (Swagger UI)

### Autenticación (`/api/auth`)
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión

### Cuenta (`/api/account`)
- `GET /api/account/status` - Estado de cuenta
- `POST /api/account/set-wallet` - Configurar wallet de Hyperliquid
- `DELETE /api/account/wallet` - Eliminar wallet
- `GET /api/account/hyperliquid/state` - Estado de cuenta en Hyperliquid

### Simulator (`/api/simulator`)
- `POST /api/simulator/config` - Crear configuración de simulador
- `GET /api/simulator/configs` - Listar configuraciones
- `GET /api/simulator/config/{id}` - Ver configuración
- `GET /api/simulator/config/{id}/positions` - Ver posiciones
- `GET /api/simulator/config/{id}/trades` - Ver trades
- `GET /api/simulator/config/{id}/stats` - Ver estadísticas
- `POST /api/simulator/trade` - Simular trade
- `POST /api/simulator/trade/close` - Cerrar trade simulado
- `DELETE /api/simulator/config/{id}` - Eliminar configuración

### Ultra Copy Trading (`/api/ultra`)
- `POST /api/ultra/config` - Crear configuración de copy trading
- `GET /api/ultra/configs` - Listar configuraciones
- `GET /api/ultra/config/{id}` - Ver configuración
- `POST /api/ultra/config/{id}/start` - Iniciar monitoreo automático
- `POST /api/ultra/config/{id}/stop` - Detener monitoreo
- `GET /api/ultra/config/{id}/positions` - Ver posiciones activas
- `GET /api/ultra/config/{id}/trades` - Ver historial de trades
- `GET /api/ultra/config/{id}/stats` - Ver estadísticas
- `POST /api/ultra/trade/execute` - Ejecutar trade manualmente (testing)
- `DELETE /api/ultra/config/{id}` - Eliminar configuración

## 📊 Ejemplo de Uso

### 1. Registrarse y Login

```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

Guarda el `access_token` que recibes.

### 2. Conectar Wallet de Hyperliquid

```bash
curl -X POST http://localhost:8000/api/account/set-wallet \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"wallet_address": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"}'
```

### 3. Usar el Simulator

```bash
# Crear configuración de simulador
curl -X POST http://localhost:8000/api/simulator/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "target_trader": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b",
    "initial_balance": 10000,
    "leverage": 5
  }'

# Simular un trade
curl -X POST http://localhost:8000/api/simulator/trade \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "config_id": "CONFIG_ID",
    "symbol": "BTC",
    "side": "LONG",
    "size": 0.1,
    "price": 50000
  }'
```

### 4. Usar Ultra Copy Trading

```bash
# Crear configuración de copy trading
curl -X POST http://localhost:8000/api/ultra/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "target_trader": "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b",
    "margin_multiplier": 1.0,
    "testnet_mode": true
  }'

# Iniciar monitoreo automático
curl -X POST http://localhost:8000/api/ultra/config/CONFIG_ID/start \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🏗️ Arquitectura del Backend Unificado

```
hyperliquid-copytrade/backend/
├── main.py                    # Aplicación principal (punto de entrada)
├── config.py                  # Configuración global
├── start.sh                   # Script de arranque
├── requirements.txt           # Dependencias Python
│
├── auth/                      # Sistema de autenticación
│   ├── security.py           # JWT y hashing
│   ├── encryption.py         # Encriptación de API keys
│   └── dependencies.py       # Dependencias de auth
│
├── models/                    # Modelos de base de datos
│   ├── database.py           # Configuración de BD
│   └── user.py               # Modelo de usuario
│
├── routes/                    # Rutas de la API
│   ├── auth.py               # Endpoints de autenticación
│   └── account.py            # Endpoints de cuenta
│
├── services/                  # Servicios externos
│   └── hyperliquid.py        # Integración con Hyperliquid API
│
└── modules/                   # Módulos de copy trading
    ├── simulator/            # Módulo de simulación
    │   ├── service.py        # Lógica de simulador
    │   └── routes.py         # Endpoints de simulador
    │
    └── ultra/                # Módulo de copy trading real
        ├── service.py        # Lógica de ultra copy
        └── routes.py         # Endpoints de ultra copy
```

## 🔐 Configuración de Variables de Entorno

Copia `.env.example` a `.env` y actualiza los valores:

```bash
# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
ALGORITHM=HS256

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:///./copytrade.db

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Hyperliquid
HYPERLIQUID_API_URL=https://api.hyperliquid.xyz/info
HYPERLIQUID_TESTNET=true
```

## 🧪 Testing

### Verificar que el servidor está corriendo

```bash
# Health check
curl http://localhost:8000/health

# Ver información de módulos
curl http://localhost:8000/
```

### Explorar la API interactivamente

Abre en tu navegador: `http://localhost:8000/docs`

Verás la documentación Swagger con todos los endpoints disponibles y podrás probarlos directamente.

## ⚠️ Diferencias entre Simulator y Ultra

| Característica | Simulator | Ultra Copy Trading |
|----------------|-----------|-------------------|
| Ejecuta trades reales | ❌ No | ✅ Sí |
| Requiere wallet conectada | ❌ No | ✅ Sí |
| Riesgo financiero | ❌ Ninguno | ⚠️ Real |
| WebSocket monitoring | ❌ No | ✅ Sí |
| Ideal para | Testing, aprendizaje | Trading real |
| Costo de fees | ❌ Ninguno | ✅ Fees reales |

## 🚧 Próximas Funcionalidades

- [ ] WebSocket real-time updates para frontend
- [ ] Dashboard visual con gráficos
- [ ] Sistema de notificaciones (email/Telegram)
- [ ] Backtesting integrado
- [ ] Risk management avanzado
- [ ] Multi-trader following
- [ ] Performance analytics
- [ ] Mobile app

## 📝 Notas Importantes

1. **Ambos módulos corren simultáneamente** en el mismo servidor
2. **No necesitas parar el servidor** para cambiar entre Simulator y Ultra
3. **Puedes usar ambos al mismo tiempo** - diferentes configuraciones pueden estar activas
4. **Ultra Copy Trading ejecuta trades REALES** - úsalo con precaución
5. **Empieza siempre con Simulator** para probar estrategias antes de usar dinero real

## 🐛 Troubleshooting

### Error: "Port 8000 already in use"

```bash
# Encuentra el proceso usando el puerto
lsof -ti:8000 | xargs kill -9

# O usa otro puerto
./start.sh --port 8001
```

### Error: "Module not found"

```bash
# Reinstala dependencias
cd hyperliquid-copytrade/backend
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Database locked"

```bash
# Elimina la base de datos y vuelve a crearla
rm copytrade.db
# El servidor la recreará automáticamente al arrancar
```

## 📞 Soporte

Para bugs o preguntas:
1. Revisa la documentación en `/docs`
2. Verifica los logs del servidor
3. Crea un issue en el repositorio

## 📄 Licencia

Este proyecto es privado y confidencial.

---

**¡Listo para empezar!** 🚀

Simplemente ejecuta:

```bash
cd hyperliquid-copytrade/backend
./start.sh --reload
```

Y tendrás ambos módulos (Simulator y Ultra) corriendo simultáneamente en `http://localhost:8000`
