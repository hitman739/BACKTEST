# Dentist Scraper - Google Places API

Script en Python para extraer información de dentistas en Alcobendas (España) usando Google Places API.

## Características

- Busca todos los dentistas en Alcobendas
- Extrae información detallada: nombre, dirección, teléfono, rating y número de reseñas
- Maneja paginación automática de resultados
- Guarda los datos en formato CSV con timestamp
- Ordena resultados por rating
- Muestra resumen con top 5 dentistas

## Requisitos

- Python 3.6 o superior
- Una API key de Google Places API

## Configuración

### 1. Obtener API Key de Google Places

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **Places API**:
   - Ve a "APIs & Services" > "Library"
   - Busca "Places API"
   - Haz clic en "Enable"
4. Crea credenciales:
   - Ve a "APIs & Services" > "Credentials"
   - Haz clic en "Create Credentials" > "API Key"
   - Copia tu API key

### 2. Instalar dependencias

```bash
pip install -r requirements_dentist_scraper.txt
```

O instalar manualmente:

```bash
pip install googlemaps
```

### 3. Configurar API Key

Configura tu API key como variable de entorno:

```bash
export GOOGLE_PLACES_API_KEY='tu_api_key_aqui'
```

O en Windows:

```cmd
set GOOGLE_PLACES_API_KEY=tu_api_key_aqui
```

Alternativamente, puedes crear un archivo `.env`:

```bash
cp .env.dentist.example .env
# Edita .env y añade tu API key
```

Y modificar el script para usar python-dotenv.

## Uso

Ejecuta el script:

```bash
python dentist_scraper.py
```

El script:
1. Buscará todos los dentistas en Alcobendas
2. Extraerá información detallada de cada uno
3. Guardará los resultados en un CSV con formato: `dentistas_alcobendas_YYYYMMDD_HHMMSS.csv`
4. Mostrará un resumen con los top 5 dentistas por rating

## Formato del CSV

El archivo CSV incluye las siguientes columnas:

- `nombre`: Nombre del dentista/clínica
- `direccion`: Dirección completa
- `telefono`: Número de teléfono
- `rating`: Calificación promedio (1-5 estrellas)
- `num_resenas`: Número total de reseñas

## Ejemplo de salida

```
============================================================
EXTRACTOR DE DENTISTAS EN ALCOBENDAS
============================================================

Buscando: dentista in Alcobendas, Spain...
Encontrados 20 resultados en la primera página

Total de lugares encontrados: 20

Extrayendo información detallada...
Procesando 20/20...

Datos guardados en: dentistas_alcobendas_20250119_143022.csv
Total de dentistas: 20

============================================================
RESUMEN
============================================================
Total de dentistas encontrados: 20

Top 5 dentistas por rating:
  1. Clínica Dental Ejemplo
     Rating: 4.8 (156 reseñas)
     Teléfono: +34 916 12 34 56

  ...
```

## Costos de API

Google Places API tiene las siguientes tarifas (verificar precios actuales):

- Text Search: ~$32 por 1,000 solicitudes
- Place Details: ~$17 por 1,000 solicitudes

El script hace:
- 1 búsqueda inicial + búsquedas de paginación (si hay más de 20 resultados)
- 1 solicitud de detalles por cada dentista encontrado

Google ofrece $200 de crédito mensual gratis, lo que suele ser suficiente para búsquedas pequeñas.

## Notas

- El script incluye delays entre solicitudes para respetar los límites de la API
- Los resultados están ordenados por rating de mayor a menor
- Si un dentista no tiene teléfono público, aparecerá como "N/A"

## Limitaciones

- La API de Google Places puede no incluir todos los dentistas existentes
- Algunos negocios pueden no tener toda la información disponible (ej: teléfono)
- Los límites de la API pueden aplicar según tu plan de Google Cloud

## Troubleshooting

**Error: "No se encontró la variable de entorno GOOGLE_PLACES_API_KEY"**
- Asegúrate de haber configurado la variable de entorno correctamente

**Error: "REQUEST_DENIED"**
- Verifica que la Places API está habilitada en tu proyecto de Google Cloud
- Verifica que tu API key es válida

**Pocos resultados**
- Google Places puede tener limitaciones en el número de resultados
- Intenta búsquedas más específicas si es necesario
