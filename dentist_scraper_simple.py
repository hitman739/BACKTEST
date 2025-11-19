#!/usr/bin/env python3
"""
Script para extraer información de dentistas en Alcobendas usando Google Places API.
Guarda los resultados en un archivo CSV con nombre, teléfono, rating y número de reseñas.
Versión usando requests directamente (sin googlemaps wrapper).
"""

import os
import csv
import time
from typing import List, Dict
import requests
from datetime import datetime


def search_places(api_key: str, query: str, location: str = None) -> List[Dict]:
    """
    Busca lugares usando Google Places API Text Search.

    Args:
        api_key: Clave de API de Google Places
        query: Búsqueda de texto
        location: Ubicación opcional (lat,lng)

    Returns:
        Lista de lugares encontrados
    """
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    all_results = []
    params = {
        "query": query,
        "key": api_key,
        "language": "es"
    }

    if location:
        params["location"] = location

    print(f"Buscando: {query}...")

    while True:
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            print(f"Error en la solicitud: {response.status_code}")
            print(f"Respuesta: {response.text}")
            break

        data = response.json()

        if data.get("status") not in ["OK", "ZERO_RESULTS"]:
            print(f"Error en la API: {data.get('status')}")
            if "error_message" in data:
                print(f"Mensaje: {data['error_message']}")
            break

        results = data.get("results", [])
        all_results.extend(results)
        print(f"Encontrados {len(results)} resultados en esta página (total: {len(all_results)})")

        # Verificar si hay más páginas
        if "next_page_token" not in data:
            break

        # Esperar antes de solicitar la siguiente página
        time.sleep(2)
        params = {
            "pagetoken": data["next_page_token"],
            "key": api_key
        }

    return all_results


def get_place_details(api_key: str, place_id: str) -> Dict:
    """
    Obtiene detalles adicionales de un lugar específico.

    Args:
        api_key: Clave de API de Google Places
        place_id: ID del lugar

    Returns:
        Diccionario con detalles del lugar
    """
    base_url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "key": api_key,
        "language": "es",
        "fields": "name,formatted_phone_number,international_phone_number,formatted_address,rating,user_ratings_total"
    }

    try:
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            return {}

        data = response.json()

        if data.get("status") == "OK":
            return data.get("result", {})

        return {}

    except Exception as e:
        print(f"Error obteniendo detalles: {e}")
        return {}


def extract_dentist_info(place: Dict, api_key: str = None) -> Dict:
    """
    Extrae la información relevante de un dentista.

    Args:
        place: Diccionario con información del lugar
        api_key: Clave de API (opcional, para obtener detalles adicionales)

    Returns:
        Diccionario con nombre, teléfono, rating y número de reseñas
    """
    info = {
        'nombre': place.get('name', 'N/A'),
        'direccion': place.get('formatted_address', 'N/A'),
        'telefono': place.get('formatted_phone_number', 'N/A'),
        'rating': place.get('rating', 'N/A'),
        'num_resenas': place.get('user_ratings_total', 0),
    }

    # Si no tenemos el teléfono y tenemos la API key, intentar obtener detalles
    if info['telefono'] == 'N/A' and api_key and 'place_id' in place:
        details = get_place_details(api_key, place['place_id'])
        if details:
            info['telefono'] = details.get('formatted_phone_number',
                                          details.get('international_phone_number', 'N/A'))
            # Actualizar otros campos si están disponibles
            if 'rating' in details:
                info['rating'] = details['rating']
            if 'user_ratings_total' in details:
                info['num_resenas'] = details['user_ratings_total']

    return info


def save_to_csv(dentists: List[Dict], filename: str = 'dentistas_alcobendas.csv'):
    """
    Guarda la información de los dentistas en un archivo CSV.

    Args:
        dentists: Lista de diccionarios con información de dentistas
        filename: Nombre del archivo CSV
    """
    if not dentists:
        print("No hay datos para guardar")
        return

    fieldnames = ['nombre', 'direccion', 'telefono', 'rating', 'num_resenas']

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dentists)

    print(f"\nDatos guardados en: {filename}")
    print(f"Total de dentistas: {len(dentists)}")


def main():
    """Función principal del script."""
    # Obtener API key desde variable de entorno o argumento
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')

    if not api_key:
        print("ERROR: No se encontró la variable de entorno GOOGLE_PLACES_API_KEY")
        print("Por favor, configura tu API key:")
        print("  export GOOGLE_PLACES_API_KEY='tu_api_key_aqui'")
        return

    print("=" * 60)
    print("EXTRACTOR DE DENTISTAS EN ALCOBENDAS")
    print("=" * 60)
    print()

    # Buscar dentistas en Alcobendas
    query = "dentista in Alcobendas, España"
    places = search_places(api_key, query)

    if not places:
        print("No se encontraron resultados")
        return

    # Extraer información detallada
    print("\nExtrayendo información detallada...")
    dentists_info = []

    for i, place in enumerate(places, 1):
        print(f"Procesando {i}/{len(places)}: {place.get('name', 'N/A')}...", end='\r')

        # Obtener detalles completos para tener el teléfono
        if 'place_id' in place:
            details = get_place_details(api_key, place['place_id'])
            # Combinar información básica con detalles
            place.update(details)
            time.sleep(0.1)  # Pequeño delay para no saturar la API

        info = extract_dentist_info(place)
        dentists_info.append(info)

    print()  # Nueva línea después del progreso

    # Ordenar por rating (de mayor a menor)
    dentists_info.sort(key=lambda x: float(x['rating']) if x['rating'] != 'N/A' else 0, reverse=True)

    # Guardar en CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'dentistas_alcobendas_{timestamp}.csv'
    save_to_csv(dentists_info, filename)

    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total de dentistas encontrados: {len(dentists_info)}")

    # Top 5 dentistas
    print("\nTop 5 dentistas por rating:")
    for i, dentist in enumerate(dentists_info[:5], 1):
        print(f"  {i}. {dentist['nombre']}")
        print(f"     Rating: {dentist['rating']} ({dentist['num_resenas']} reseñas)")
        print(f"     Teléfono: {dentist['telefono']}")
        print()


if __name__ == '__main__':
    main()
