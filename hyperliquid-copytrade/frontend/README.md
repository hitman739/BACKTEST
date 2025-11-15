# Frontend - Hyperliquid CopyTrading

Frontend simple creado con Vite + React.

## Instalación

```bash
npm install
```

## Ejecutar en desarrollo

```bash
npm run dev
```

La app se abrirá en `http://localhost:5173`

## Build para producción

```bash
npm run build
```

## Configuración

El frontend se conecta al backend en:
```
http://127.0.0.1:8000
```

Si necesitas cambiar la URL del backend, edita `src/App.jsx`:
```javascript
const API_URL = 'http://127.0.0.1:8000'
```

## Endpoints usados

- `POST /start` - Iniciar copytrading
- `POST /stop` - Detener copytrading
- `GET /status` - Obtener estado actual

## Estructura

```
frontend/
├── index.html          # HTML principal
├── package.json        # Dependencias
├── vite.config.js      # Configuración Vite
└── src/
    ├── main.jsx        # Punto de entrada
    ├── App.jsx         # Componente principal
    └── index.css       # Estilos globales
```

## Requisitos

- Node.js 18+
- npm o yarn
- Backend corriendo en http://127.0.0.1:8000
