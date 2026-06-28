from datetime import datetime, timedelta
from flask import request

def es_dni (dni):
    return dni.isnumeric() and (len(dni) > 6) and (len(dni) < 9)

def devolver_hora_fin (horario, duracion):

    finalizacion = (
        datetime.combine(
            datetime.today(),
            horario
        )
        + timedelta(minutes=duracion)
    ).time()

    return finalizacion

def devolver_enlace_absoluto_actual ():

    import os

    URL = ""
    
    # 1. Intentamos obtener la URL pública real consultando directamente a los túneles activos de ngrok
    try:
        from pyngrok import ngrok
        tunnels = ngrok.get_tunnels()
        if tunnels:
            URL = tunnels[0].public_url
    except Exception:
        pass
    
    # 2. Si falla, obtenemos la URL de Ngrok del archivo .env
    if not URL:
        URL = os.environ.get('URL_NGROK', '')
        
    # Si no hay URL de Ngrok, usamos la URL base de la petición actual para evitar rutas relativas
    if not URL:
        URL = request.url_root
        
    URL = URL.rstrip('/')

    return URL