#!/usr/bin/env python3
"""
Scraper de dentistas en Alcobendas usando Playwright para Google Maps.
No requiere API key - extrae datos directamente de Google Maps.
"""

import csv
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def scroll_page(page, scrolls=5):
    """Hace scroll en la página para cargar más resultados."""
    for i in range(scrolls):
        # Scroll en el panel de resultados
        page.evaluate("""
            const panel = document.querySelector('[role="feed"]');
            if (panel) {
                panel.scrollTop = panel.scrollHeight;
            }
        """)
        time.sleep(2)


def extract_rating(rating_text):
    """Extrae el rating numérico del texto."""
    if not rating_text:
        return 'N/A'
    match = re.search(r'(\d+[,.]?\d*)', rating_text)
    if match:
        return match.group(1).replace(',', '.')
    return 'N/A'


def extract_reviews_count(reviews_text):
    """Extrae el número de reseñas del texto."""
    if not reviews_text:
        return 0
    # Buscar números entre paréntesis o después de texto
    match = re.search(r'[(\[]?(\d+)[)\]]?', reviews_text)
    if match:
        return int(match.group(1))
    return 0


def scrape_google_maps_dentists(city="Alcobendas", max_results=100):
    """
    Scrape dentistas de Google Maps.

    Args:
        city: Ciudad donde buscar
        max_results: Número máximo de resultados a extraer

    Returns:
        Lista de diccionarios con información de dentistas
    """
    print("=" * 60)
    print("SCRAPER DE DENTISTAS EN GOOGLE MAPS")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        # Lanzar navegador
        print("Iniciando navegador...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        # Buscar dentistas en Google Maps
        search_query = f"dentistas en {city}, España"
        google_maps_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"

        print(f"Buscando: {search_query}")
        print(f"URL: {google_maps_url}")
        print()

        page.goto(google_maps_url, wait_until='networkidle', timeout=60000)

        # Esperar a que carguen los resultados
        print("Esperando resultados...")
        try:
            page.wait_for_selector('div[role="feed"]', timeout=15000)
        except PlaywrightTimeout:
            print("No se encontró el panel de resultados. Intentando de todas formas...")

        time.sleep(3)

        # Rechazar cookies si aparece el diálogo
        try:
            reject_button = page.locator('button:has-text("Rechazar todo"), button:has-text("Reject all")')
            if reject_button.count() > 0:
                reject_button.first.click()
                time.sleep(1)
        except:
            pass

        # Hacer scroll para cargar más resultados
        print("Cargando más resultados (esto puede tomar un momento)...")
        scroll_page(page, scrolls=10)

        # Extraer todos los elementos de lugar
        print("\nExtrayendo información de dentistas...")
        dentists = []

        # Diferentes selectores para los resultados
        selectors = [
            'div[role="feed"] > div > div[role="article"]',
            'div[role="feed"] > div > div',
            'a[href*="/maps/place/"]'
        ]

        places = None
        for selector in selectors:
            places = page.locator(selector).all()
            if len(places) > 0:
                print(f"Encontrados {len(places)} lugares con selector: {selector}")
                break

        if not places:
            print("ERROR: No se pudieron encontrar resultados")
            browser.close()
            return []

        # Procesar cada lugar
        for i, place in enumerate(places[:max_results]):
            try:
                # Hacer clic en el lugar para abrir detalles
                place.click()
                time.sleep(1.5)

                # Extraer información
                info = {
                    'nombre': 'N/A',
                    'direccion': 'N/A',
                    'telefono': 'N/A',
                    'rating': 'N/A',
                    'num_resenas': 0
                }

                # Nombre
                try:
                    name_elem = page.locator('h1').first
                    if name_elem.count() > 0:
                        info['nombre'] = name_elem.inner_text().strip()
                except:
                    pass

                # Rating y reseñas
                try:
                    # Buscar el rating (puede estar en diferentes formatos)
                    rating_selectors = [
                        'div[role="img"][aria-label*="estrellas"]',
                        'span[role="img"][aria-label*="estrellas"]',
                        'div:has-text("estrellas")',
                        'span.fontDisplayLarge'
                    ]

                    for sel in rating_selectors:
                        rating_elem = page.locator(sel).first
                        if rating_elem.count() > 0:
                            rating_text = rating_elem.get_attribute('aria-label') or rating_elem.inner_text()
                            info['rating'] = extract_rating(rating_text)
                            break

                    # Número de reseñas
                    reviews_selectors = [
                        'button[aria-label*="opiniones"]',
                        'button[aria-label*="reseñas"]',
                        'button:has-text("opiniones")',
                        'button:has-text("reseñas")'
                    ]

                    for sel in reviews_selectors:
                        reviews_elem = page.locator(sel).first
                        if reviews_elem.count() > 0:
                            reviews_text = reviews_elem.get_attribute('aria-label') or reviews_elem.inner_text()
                            info['num_resenas'] = extract_reviews_count(reviews_text)
                            break

                except:
                    pass

                # Dirección
                try:
                    address_elem = page.locator('button[data-item-id*="address"]').first
                    if address_elem.count() > 0:
                        info['direccion'] = address_elem.get_attribute('aria-label') or address_elem.inner_text()
                        info['direccion'] = info['direccion'].replace('Dirección: ', '').strip()
                except:
                    pass

                # Teléfono
                try:
                    phone_selectors = [
                        'button[data-item-id*="phone:tel:"]',
                        'button[aria-label*="Teléfono"]',
                        'a[href^="tel:"]'
                    ]

                    for sel in phone_selectors:
                        phone_elem = page.locator(sel).first
                        if phone_elem.count() > 0:
                            phone_text = phone_elem.get_attribute('aria-label') or phone_elem.inner_text()
                            # Extraer solo el número
                            phone_match = re.search(r'[\d\s\+]+', phone_text)
                            if phone_match:
                                info['telefono'] = phone_match.group(0).strip()
                            break
                except:
                    pass

                # Solo agregar si tiene al menos un nombre válido
                if info['nombre'] != 'N/A':
                    dentists.append(info)
                    print(f"  {len(dentists)}. {info['nombre']} - Rating: {info['rating']} ({info['num_resenas']} reseñas)")

                # No procesar demasiados
                if len(dentists) >= max_results:
                    break

            except Exception as e:
                print(f"Error procesando lugar {i+1}: {e}")
                continue

        browser.close()

    return dentists


def save_to_csv(dentists, filename='dentistas_alcobendas.csv'):
    """Guarda los dentistas en un archivo CSV."""
    if not dentists:
        print("\nNo hay datos para guardar")
        return

    fieldnames = ['nombre', 'direccion', 'telefono', 'rating', 'num_resenas']

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dentists)

    print(f"\n✓ Datos guardados en: {filename}")
    print(f"✓ Total de dentistas: {len(dentists)}")


def main():
    """Función principal."""
    try:
        # Scrape dentistas
        dentists = scrape_google_maps_dentists(city="Alcobendas", max_results=50)

        if not dentists:
            print("\n⚠ No se encontraron dentistas")
            return

        # Ordenar por rating
        dentists.sort(
            key=lambda x: (
                float(x['rating']) if x['rating'] != 'N/A' else 0,
                x['num_resenas']
            ),
            reverse=True
        )

        # Guardar en CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dentistas_alcobendas_{timestamp}.csv'
        save_to_csv(dentists, filename)

        # Mostrar resumen
        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"Total de dentistas: {len(dentists)}")

        # Top 5
        print("\nTop 5 dentistas por rating:")
        for i, dentist in enumerate(dentists[:5], 1):
            print(f"\n  {i}. {dentist['nombre']}")
            print(f"     Rating: {dentist['rating']} ⭐ ({dentist['num_resenas']} reseñas)")
            print(f"     Teléfono: {dentist['telefono']}")
            print(f"     Dirección: {dentist['direccion'][:60]}...")

        print("\n" + "=" * 60)
        print("✓ SCRAPING COMPLETADO")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error durante el scraping: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
