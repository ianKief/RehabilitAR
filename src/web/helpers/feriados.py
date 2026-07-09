import json
import urllib.request
from datetime import date, timedelta

# Caché en memoria para no saturar la API externa ni enlentecer la carga de la página
_CACHE_FERIADOS = {}

def _obtener_feriados_api(year: int) -> list:
    """
    Función interna que obtiene los feriados del año desde una API externa
    y los cachea en memoria para mejorar el rendimiento en llamadas sucesivas.
    """
    if year in _CACHE_FERIADOS:
        return _CACHE_FERIADOS[year]
    
    feriados = []
    try:
        url = f"https://api.argentinadatos.com/v1/feriados/{year}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            feriados = [item.get('fecha') for item in data if 'fecha' in item]
            _CACHE_FERIADOS[year] = feriados
    except Exception as e:
        print(f"Advertencia: No se pudieron cargar los feriados de la API: {e}")
        # Si la API falla, usamos un fallback de emergencia para no romper la funcionalidad
        feriados = [f"{year}-12-25", f"{year}-01-01"] 
    return feriados

def obtener_dias_no_laborables(year: int) -> list:
    """
    Obtiene los feriados desde la API y calcula todos los sábados y domingos del año.
    Devuelve una lista combinada de fechas en formato 'YYYY-MM-DD'.
    """
    feriados = _obtener_feriados_api(year)
    fines_de_semana = []
    
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    delta = timedelta(days=1)
    
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() in [5, 6]:
            fines_de_semana.append(current_date.strftime('%Y-%m-%d'))
        current_date += delta
        
    return list(set(feriados + fines_de_semana))