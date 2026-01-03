# ⌚ LAPOMETRO

**La forma más rápida de valorar relojes usados** basándose en ventas reales de eBay.

---

## ✨ Funcionalidades

### 🔍 Búsqueda Inteligente
- **Búsqueda por texto**: Escribe marca y modelo
- **Subir foto**: Sube una imagen de tu reloj para búsqueda automática

### 📊 Análisis de Mercado
- **Ventas reales**: Datos de eBay actualizados en tiempo real
- **Estadísticas completas**:
  - Precio medio del mercado
  - Rango de precios (mínimo - máximo)
  - Número de ventas encontradas
  - Estimación del valor actual
- **Gráfico de evolución**: Visualiza cómo han cambiado los precios en el tiempo
- **Listado detallado**: Ver ventas recientes con imágenes, condición, fecha y enlaces directos

### 🔐 Sistema de Autenticación
- Login seguro con NextAuth.js
- Cuenta demo incluida para pruebas
- Sesiones persistentes

### 🎨 Diseño Premium
- **Branding negro y rosa** con gradientes vibrantes
- **Background animado** con efectos de movimiento y glow
- **UI moderna** con efectos glassmorphism y hover states
- **Totalmente responsiva**

---

## 🚀 Instalación Rápida

### Prerrequisitos
- Node.js 18+
- Cuenta de desarrollador de eBay (opcional, incluye modo demo)

### 1. Clonar e instalar

```bash
git clone https://github.com/hitman739/BACKTEST.git
cd BACKTEST/watch-valuation
npm install
```

### 2. Configurar variables de entorno

```bash
cp .env.local.example .env.local
```

El archivo `.env.local` debe contener:

```env
# eBay API
EBAY_APP_ID=demo  # O tu propia API key de https://developer.ebay.com/

# NextAuth
NEXTAUTH_SECRET=your-secret-key-change-this
NEXTAUTH_URL=http://localhost:3000
```

### 3. Ejecutar en desarrollo

```bash
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000) en tu navegador.

### 4. Iniciar sesión (opcional)

**Cuenta Demo:**
- Email: `demo@lapometro.com`
- Contraseña: `demo123`

---

## 📖 Cómo Usar

### Búsqueda por Texto
1. Selecciona "Buscar por Texto"
2. Escribe marca y modelo (ej: "Rolex Submariner", "Omega Speedmaster")
3. Haz clic en "Buscar"
4. Revisa las estadísticas, gráfico y ventas recientes

### Búsqueda por Foto
1. Selecciona "Subir Foto"
2. Arrastra o selecciona una imagen de tu reloj
3. La app intentará identificar el modelo automáticamente
4. Refina la búsqueda si es necesario

---

## 🛠️ Stack Tecnológico

| Tecnología | Uso |
|-----------|-----|
| **Next.js 16** | Framework React con App Router |
| **React 19** | UI y componentes |
| **NextAuth.js** | Autenticación |
| **Recharts** | Gráficos interactivos |
| **Axios** | HTTP client |
| **bcryptjs** | Hash de contraseñas |
| **eBay Finding API** | Datos de ventas reales |

---

## 📁 Estructura del Proyecto

```
watch-valuation/
├── app/
│   ├── api/
│   │   ├── auth/
│   │   │   └── [...nextauth]/
│   │   │       └── route.js         # Configuración NextAuth
│   │   ├── ebay/
│   │   │   └── route.js             # API endpoint eBay
│   │   └── analyze-image/
│   │       └── route.js             # Análisis de imágenes
│   ├── auth/
│   │   └── signin/
│   │       └── page.js              # Página de login
│   ├── globals.css                  # Estilos globales + animaciones
│   ├── layout.js                    # Layout principal
│   ├── page.js                      # Página principal
│   └── providers.js                 # SessionProvider
├── .env.local                       # Variables de entorno (git ignored)
├── .env.local.example              # Ejemplo de configuración
├── .gitignore
├── package.json
└── README.md
```

---

## 🎨 Personalización de Diseño

### Colores del Brand

Los colores principales están definidos en el código:

- **Rosa Principal**: `#ff1493` (Deep Pink)
- **Rosa Claro**: `#ff69b4` (Hot Pink)
- **Rosa Oscuro**: `#c71585` (Medium Violet Red)
- **Negro**: `#000000`

### Background Animado

El background usa gradientes animados con CSS keyframes:
- Gradiente que se mueve suavemente (15s loop)
- Efectos de glow pulsantes (8s loop)
- Degradados radiales con opacidad variable

Puedes ajustar las animaciones en `app/globals.css`:

```css
@keyframes gradientShift { ... }
@keyframes pulseGlow { ... }
```

---

## 🔧 API de eBay

### Configuración

1. Ve a [eBay Developers Program](https://developer.ebay.com/)
2. Crea una aplicación
3. Obtén tu **App ID** (también llamado Client ID)
4. Añádelo a `.env.local`:

```env
EBAY_APP_ID=tu_app_id_aqui
```

### Límites de la API

| Tier | Llamadas/día |
|------|-------------|
| Sandbox | 5,000 |
| Production (gratis) | 5,000 |

Para más llamadas, contacta con eBay para un plan enterprise.

### Endpoint Usado

```
GET https://svcs.ebay.com/services/search/FindingService/v1
```

**Operación**: `findCompletedItems`
- Filtra solo artículos vendidos
- Hasta 100 resultados por búsqueda
- Ordenados por fecha de finalización

---

## 🔐 Autenticación

### Configuración de NextAuth

La app usa **NextAuth.js** con el provider de credenciales.

**Para producción**, considera:
1. Cambiar `NEXTAUTH_SECRET` a un valor seguro:
   ```bash
   openssl rand -base64 32
   ```

2. Usar una base de datos real (MongoDB, PostgreSQL, etc.)

3. Añadir más providers (Google, GitHub, etc.):
   ```js
   import GoogleProvider from 'next-auth/providers/google';

   providers: [
     GoogleProvider({
       clientId: process.env.GOOGLE_CLIENT_ID,
       clientSecret: process.env.GOOGLE_CLIENT_SECRET,
     }),
   ]
   ```

### Usuarios de Demo

Por defecto incluye un usuario demo:
- **Email**: demo@lapometro.com
- **Contraseña**: demo123

Para añadir más usuarios, edita:
`app/api/auth/[...nextauth]/route.js`

---

## 📸 Análisis de Imágenes (TODO)

El endpoint de análisis de imágenes actualmente está en modo placeholder.

### Para implementar OCR/Visión:

**Opción 1: Google Cloud Vision API**
```bash
npm install @google-cloud/vision
```

**Opción 2: Tesseract.js (OCR local)**
```bash
npm install tesseract.js
```

**Opción 3: OpenAI Vision API**
```bash
npm install openai
```

Edita `app/api/analyze-image/route.js` para integrar tu solución preferida.

---

## 🚀 Deployment

### Vercel (Recomendado)

1. Sube tu código a GitHub
2. Ve a [vercel.com](https://vercel.com)
3. Importa tu repositorio
4. Añade las variables de entorno:
   - `EBAY_APP_ID`
   - `NEXTAUTH_SECRET`
   - `NEXTAUTH_URL` (tu dominio de producción)
5. Deploy automático

### Otras opciones
- **Netlify**: Soporta Next.js
- **Railway**: Deploy con un click
- **Docker**: Usa `Dockerfile` estándar de Next.js

---

## 💡 Mejoras Futuras

- [ ] OCR real para análisis de imágenes
- [ ] Registro de usuarios (signup)
- [ ] Base de datos para guardar búsquedas favoritas
- [ ] Alertas de precio por email/notificación
- [ ] Comparar múltiples modelos lado a lado
- [ ] Exportar reportes a PDF
- [ ] Soporte para más marketplaces (Chrono24, WatchBox)
- [ ] API pública para desarrolladores
- [ ] App móvil nativa (React Native)
- [ ] Sistema de valoración por IA

---

## 🐛 Troubleshooting

### La app no encuentra datos de eBay

1. Verifica que `EBAY_APP_ID` esté configurado
2. Prueba con búsquedas genéricas: `rolex`, `omega watch`
3. Revisa la consola del navegador (F12) para errores de red
4. Verifica que la API de eBay esté disponible

### Error de autenticación

1. Asegúrate de que `NEXTAUTH_SECRET` esté configurado
2. Verifica que `NEXTAUTH_URL` coincida con tu URL local
3. Limpia las cookies del navegador
4. Reinicia el servidor de desarrollo

### El background animado no se ve

1. Asegúrate de que `app/globals.css` esté importado en `app/layout.js`
2. Verifica que tu navegador soporte CSS animations
3. Desactiva extensiones de navegador que puedan bloquear CSS

---

## 📄 Licencia

ISC

---

## 🤝 Contribuciones

¿Tienes ideas? Abre un issue o pull request.

### Desarrollar localmente

```bash
git checkout -b feature/mi-nueva-feature
# ... haz cambios ...
git commit -m "Add: mi nueva feature"
git push origin feature/mi-nueva-feature
```

---

## 👨‍💻 Autor

Creado con 🖤 y 💗 por el equipo de LAPOMETRO

**LAPOMETRO** - La forma más rápida de saber cuánto vale tu reloj.

---

### Ejemplos de Búsqueda

Prueba con estos modelos populares:
- Rolex Submariner
- Omega Speedmaster
- Seiko SKX007
- Tag Heuer Carrera
- Patek Philippe Nautilus
- Audemars Piguet Royal Oak
- Casio G-Shock
- Tudor Black Bay
