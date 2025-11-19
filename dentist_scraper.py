#!/usr/bin/env python3
"""
Script para extraer información de dentistas en Alcobendas usando Google Places API.
Guarda los resultados en un archivo CSV con nombre, teléfono, rating y número de reseñas.
"""

import os
import csv
import time
from typing import List, Dict
import googlemaps
from datetime import datetime


def get_dentists_in_alcobendas(api_key: str) -> List[Dict]:
    """
    Busca todos los dentistas en Alcobendas usando Google Places API.

    Args:
        api_key: Clave de API de Google Places

    Returns:
        Lista de diccionarios con información de cada dentista
    """
    gmaps = googlemaps.Client(key=api_key)

    # Buscar dentistas en Alcobendas
    query = "dentista in Alcobendas, Spain"

    print(f"Buscando: {query}...")

    all_results = []

    # Primera búsqueda
    places_result = gmaps.places(query=query, language='es')

    # Procesar resultados de la primera página
    all_results.extend(places_result.get('results', []))
    print(f"Encontrados {len(places_result.get('results', []))} resultados en la primera página")

    # Obtener páginas adicionales si existen
    while 'next_page_token' in places_result:
        # Google requiere un pequeño delay antes de usar el next_page_token
        time.sleep(2)

        next_page_token = places_result['next_page_token']
        places_result = gmaps.places(query=query, page_token=next_page_token, language='es')

        new_results = places_result.get('results', [])
        all_results.extend(new_results)
        print(f"Encontrados {len(new_results)} resultados adicionales")

    print(f"\nTotal de lugares encontrados: {len(all_results)}")

    return all_results


def get_place_details(gmaps: googlemaps.Client, place_id: str) -> Dict:
    """
    Obtiene detalles adicionales de un lugar específico.

    Args:
        gmaps: Cliente de Google Maps
        place_id: ID del lugar

    Returns:
        Diccionario con detalles del lugar
    """
    try:
        details = gmaps.place(place_id=place_id, language='es')
        return details.get('result', {})
    except Exception as e:
        print(f"Error obteniendo detalles para {place_id}: {e}")
        return {}


def extract_dentist_info(place: Dict, gmaps: googlemaps.Client = None) -> Dict:
    """
    Extrae la información relevante de un dentista.

    Args:
        place: Diccionario con información del lugar
        gmaps: Cliente de Google Maps (opcional, para obtener detalles adicionales)

    Returns:
        Diccionario con nombre, teléfono, rating y número de reseñas
    """
    info = {
        'nombre': place.get('name', 'N/A'),
        'direccion': place.get('formatted_address', place.get('vicinity', 'N/A')),
        'telefono': place.get('formatted_phone_number', 'N/A'),
        'rating': place.get('rating', 'N/A'),
        'num_resenas': place.get('user_ratings_total', 0),
    }

    # Si no tenemos el teléfono, intentar obtener detalles adicionales
    if info['telefono'] == 'N/A' and gmaps and 'place_id' in place:
        details = get_place_details(gmaps, place['place_id'])
        info['telefono'] = details.get('formatted_phone_number', 'N/A')

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
    # Obtener API key desde variable de entorno
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

    # Buscar dentistas
    places = get_dentists_in_alcobendas(api_key)

    if not places:
        print("No se encontraron resultados")
        return

    # Crear cliente para detalles adicionales
    gmaps = googlemaps.Client(key=api_key)

    # Extraer información detallada
    print("\nExtrayendo información detallada...")
    dentists_info = []

    for i, place in enumerate(places, 1):
        print(f"Procesando {i}/{len(places)}: {place.get('name', 'N/A')}...", end='\r')

        # Obtener detalles completos para tener el teléfono
        if 'place_id' in place:
            details = get_place_details(gmaps, place['place_id'])
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
