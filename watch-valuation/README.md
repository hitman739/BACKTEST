# ⌚ Valorador de Relojes

Aplicación web simple para valorar relojes usados basándose en ventas reales de eBay.

## 🎯 Funcionalidades

- **Búsqueda por texto**: Busca cualquier marca y modelo de reloj
- **Ventas reales**: Muestra ventas completadas reales de eBay
- **Estadísticas de mercado**:
  - Precio medio
  - Rango de precios (mínimo - máximo)
  - Número de ventas encontradas
  - Estimación del valor actual
- **Gráfico de evolución**: Visualiza cómo han evolucionado los precios en el tiempo
- **Listado detallado**: Ver las ventas recientes con imágenes, condición y enlaces

## 🚀 Instalación y Configuración

### Prerrequisitos

- Node.js 18+ instalado
- Cuenta de desarrollador de eBay (para producción)

### 1. Instalar dependencias

```bash
npm install
```

### 2. Configurar credenciales de eBay

#### Opción A: Modo Demo (para pruebas rápidas)

La aplicación viene con un App ID de demo de eBay que permite hacer algunas peticiones limitadas. No necesitas hacer nada, ya está configurado en `.env.local`.

#### Opción B: Usar tu propia API key (recomendado para uso real)

1. Ve a [eBay Developers Program](https://developer.ebay.com/)
2. Crea una cuenta si no tienes una
3. Ve a "My Account" → "Application Keys"
4. Crea una nueva app en el sandbox (o production)
5. Copia tu **App ID (Client ID)**
6. Edita el archivo `.env.local`:

```bash
EBAY_APP_ID=tu_app_id_aqui
```

### 3. Ejecutar en modo desarrollo

```bash
npm run dev
```

La aplicación estará disponible en [http://localhost:3000](http://localhost:3000)

### 4. Compilar para producción

```bash
npm run build
npm start
```

## 📖 Cómo usar

1. Abre la aplicación en tu navegador
2. Escribe la marca y modelo del reloj que quieres valorar
   - Ejemplos: "Rolex Submariner", "Omega Speedmaster", "Seiko SKX007"
3. Haz clic en "Buscar"
4. Revisa:
   - El precio medio del mercado
   - El rango de precios
   - El gráfico de evolución de precios
   - Las ventas recientes con detalles

## 🛠️ Stack Tecnológico

- **Framework**: Next.js 16 (App Router)
- **UI**: React 19 con CSS inline
- **Gráficos**: Recharts
- **HTTP Client**: Axios
- **API**: eBay Finding API (findCompletedItems)

## 📁 Estructura del Proyecto

```
watch-valuation/
├── app/
│   ├── api/
│   │   └── ebay/
│   │       └── route.js       # API endpoint para consultar eBay
│   ├── layout.js              # Layout principal de Next.js
│   └── page.js                # Página principal con búsqueda y resultados
├── .env.local                 # Variables de entorno (Git ignored)
├── .env.local.example         # Ejemplo de configuración
├── .gitignore
├── package.json
└── README.md
```

## 🔧 API de eBay

La aplicación usa la **eBay Finding API** con la operación `findCompletedItems`:

- Filtra solo artículos vendidos (`SoldItemsOnly`)
- Obtiene hasta 100 resultados por búsqueda
- Ordenados por fecha de finalización
- Incluye información de precio, condición, imágenes y enlaces

### Límites de la API

- **Sandbox (desarrollo)**: 5,000 llamadas/día
- **Production**: 5,000 llamadas/día (gratis)
- Para más llamadas, contacta con eBay

## 💡 Mejoras Futuras Posibles

- [ ] Filtros avanzados (condición, rango de precios)
- [ ] Comparación de múltiples modelos
- [ ] Historial de búsquedas
- [ ] Alertas de precio
- [ ] Soporte para más marketplaces
- [ ] Exportar datos a CSV/PDF
- [ ] Autenticación de usuarios
- [ ] Favoritos y watchlists

## ⚠️ Notas Importantes

1. **Datos en tiempo real**: Los precios se obtienen directamente de eBay y reflejan ventas reales completadas
2. **Sin scraping**: La aplicación usa exclusivamente APIs oficiales de eBay
3. **Limitaciones**: Los resultados dependen de la disponibilidad de datos en eBay para ese modelo específico
4. **Mercado**: Los precios son principalmente del mercado de EE.UU. (eBay.com)

## 📄 Licencia

ISC

## 🤝 Contribuciones

Este es un MVP. Siéntete libre de hacer fork y mejorar la aplicación.

---

Desarrollado con ❤️ usando Next.js y la eBay Finding API
