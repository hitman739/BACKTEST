# 🚀 Quick Start - Hyperliquid Copy Trading

Guía rápida para poner en marcha la aplicación en 5 minutos.

## Paso 1: Instalar Backend

```bash
cd hyperliquid-copytrade/backend
pip install -r requirements.txt
cp .env.example .env
python main.py
```

✅ Backend corriendo en http://localhost:8000

## Paso 2: Instalar Frontend

En otra terminal:

```bash
cd hyperliquid-copytrade/frontend
npm install
npm run dev
```

✅ Frontend corriendo en http://localhost:5173

## Paso 3: Usar la Aplicación

1. **Abre el navegador** → http://localhost:5173

2. **Regístrate**:
   - Haz clic en "Register"
   - Email: `demo@example.com`
   - Password: `demo1234`
   - Clic en "Create account"

3. **Conecta tu Wallet**:
   - En el dashboard, ingresa tu wallet de Hyperliquid
   - Formato: `0x...` (42 caracteres)
   - Ejemplo: `0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b`
   - Clic en "Connect Wallet"

🎉 ¡Listo! Tu wallet está conectada y validada.

## Verificar que Todo Funciona

### Test 1: Backend Health Check
```bash
curl http://localhost:8000/health
# Debería devolver: {"status": "healthy"}
```

### Test 2: Registro de Usuario
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test1234"}'
```

### Test 3: Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test1234"}'
```

## Estructura de URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI automática)
- **Health Check**: http://localhost:8000/health

## Problemas Comunes

### Error: Puerto 8000 en uso
```bash
# Mata el proceso existente
lsof -ti:8000 | xargs kill -9
# O usa otro puerto
uvicorn main:app --port 8001
```

### Error: Puerto 5173 en uso
```bash
# En vite.config.js, cambia el puerto
server: {
  port: 3000  // Cambiar aquí
}
```

### Error: "Module not found"
```bash
# Backend
pip install -r requirements.txt

# Frontend
rm -rf node_modules package-lock.json
npm install
```

## Siguientes Pasos

- Lee el [README.md](./README.md) completo para más detalles
- Explora la documentación automática en http://localhost:8000/docs
- Revisa el código en `backend/` y `frontend/src/`

## Demo Rápido

Usa estos datos de prueba:

**Usuario Demo**:
- Email: `demo@example.com`
- Password: `demo1234`

**Wallet de Prueba** (vault real de Hyperliquid):
```
0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b
```

---

**Tiempo estimado**: 5 minutos ⏱️
