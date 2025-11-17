# Hyperliquid Copy Trading App

Sistema de copy trading para Hyperliquid con autenticación de usuarios y gestión de wallets.

## 🚀 Características

- **Autenticación de usuarios**: Sistema completo de registro/login con JWT
- **Gestión de wallets**: Conecta tu wallet de Hyperliquid de forma segura
- **Validación en tiempo real**: Verifica automáticamente las wallets contra la API de Hyperliquid
- **Interfaz moderna**: UI con React, TailwindCSS y diseño responsivo
- **Backend robusto**: FastAPI con SQLAlchemy y encriptación de datos sensibles

## 📋 Requisitos

- Python 3.10+
- Node.js 18+
- npm o yarn

## 🛠️ Instalación

### Backend

1. Navega al directorio del backend:
```bash
cd hyperliquid-copytrade/backend
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Crea el archivo `.env` copiando el ejemplo:
```bash
cp .env.example .env
```

4. Genera claves secretas seguras:
```bash
# En Python
python -c "import secrets; print(secrets.token_hex(32))"
```

Actualiza `SECRET_KEY` y `ENCRYPTION_KEY` en tu archivo `.env`.

5. Inicia el servidor:
```bash
python main.py
```

El backend estará disponible en `http://localhost:8000`

### Frontend

1. Navega al directorio del frontend:
```bash
cd hyperliquid-copytrade/frontend
```

2. Instala las dependencias:
```bash
npm install
```

3. Inicia el servidor de desarrollo:
```bash
npm run dev
```

El frontend estará disponible en `http://localhost:5173`

## 📖 Uso

### 1. Registro de Usuario

1. Abre `http://localhost:5173` en tu navegador
2. Haz clic en "Register"
3. Ingresa tu email y contraseña (mínimo 8 caracteres, debe incluir letras y números)
4. Haz clic en "Create account"

### 2. Login

1. En la página de login, ingresa tu email y contraseña
2. Haz clic en "Sign in"
3. Serás redirigido al dashboard

### 3. Conectar Wallet de Hyperliquid

1. En el dashboard, encontrarás la sección "Connect Hyperliquid Wallet"
2. Ingresa tu dirección de wallet de Hyperliquid (formato: `0x...`)
3. Haz clic en "Connect Wallet"
4. El sistema validará automáticamente que la wallet existe en Hyperliquid

Ejemplo de wallet válida:
```
0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b
```

## 🏗️ Arquitectura

### Backend (FastAPI)

```
backend/
├── auth/
│   ├── security.py          # JWT y hashing de contraseñas
│   ├── encryption.py        # Encriptación de API keys
│   └── dependencies.py      # Dependencias de autenticación
├── models/
│   ├── database.py          # Configuración de base de datos
│   └── user.py              # Modelo de usuario
├── routes/
│   ├── auth.py              # Endpoints de autenticación
│   └── account.py           # Gestión de cuenta y wallet
├── services/
│   └── hyperliquid.py       # Integración con Hyperliquid API
├── config.py                # Configuración global
└── main.py                  # Aplicación principal
```

### Frontend (React + Vite)

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js        # Cliente Axios configurado
│   ├── components/
│   │   ├── LoginForm.jsx    # Formulario de login
│   │   ├── RegisterForm.jsx # Formulario de registro
│   │   ├── WalletSetup.jsx  # Configuración de wallet
│   │   └── ProtectedRoute.jsx
│   ├── pages/
│   │   ├── Login.jsx        # Página de login/registro
│   │   └── Dashboard.jsx    # Dashboard principal
│   ├── App.jsx
│   └── main.jsx
└── index.html
```

## 🔐 Seguridad

- **Contraseñas**: Hasheadas con bcrypt
- **Tokens**: JWT con expiración configurable
- **API Keys**: Encriptadas con Fernet (AES-128-CBC)
- **CORS**: Configurado solo para orígenes permitidos
- **Validación**: Input validation en backend y frontend

## 🔌 API Endpoints

### Autenticación

- `POST /api/auth/register` - Registrar nuevo usuario
- `POST /api/auth/login` - Iniciar sesión

### Cuenta

- `GET /api/account/status` - Estado de la cuenta (requiere auth)
- `POST /api/account/set-wallet` - Configurar wallet de Hyperliquid (requiere auth)
- `DELETE /api/account/wallet` - Eliminar wallet (requiere auth)
- `GET /api/account/hyperliquid/state` - Estado de la cuenta en Hyperliquid (requiere auth)

### Health

- `GET /` - Información de la API
- `GET /health` - Health check

## 🧪 Testing

### Testear el Backend

```bash
cd backend
python -c "from models.database import init_db; init_db()"
python main.py
```

Luego en otra terminal:

```bash
# Registrar usuario
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test1234"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test1234"}'
```

## 📝 Configuración de Variables de Entorno

### Backend (.env)

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

## 🚧 Próximas Funcionalidades

- [ ] Copy trading en tiempo real
- [ ] WebSocket para seguimiento de trades
- [ ] Dashboard con estadísticas de traders
- [ ] Configuración de estrategias de copy trading
- [ ] Sistema de notificaciones
- [ ] Gestión de riesgos avanzada
- [ ] Historial de trades copiados
- [ ] Métricas de performance

## 📄 Licencia

Este proyecto es privado y confidencial.

## 🤝 Contribuir

Para contribuir al proyecto:

1. Crea una rama feature: `git checkout -b feature/nueva-funcionalidad`
2. Commit tus cambios: `git commit -m 'Add nueva funcionalidad'`
3. Push a la rama: `git push origin feature/nueva-funcionalidad`
4. Abre un Pull Request

## 🐛 Reportar Bugs

Si encuentras algún bug, por favor crea un issue con:

- Descripción del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Screenshots (si aplica)
- Información del entorno (OS, browser, versiones)

## 📞 Soporte

Para soporte o preguntas, contacta al equipo de desarrollo.
