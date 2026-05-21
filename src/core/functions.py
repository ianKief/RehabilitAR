from sqlalchemy import func, text
from src.core.clases.clases import Clase

def filtro_clase_actual ():
    """Devuelve dos filtros para agarrar una clase actual. Para usar, hacer .filter(*filtro_clase_actual())"""
    return [
        (func.now() > Clase.fecha_hora)
        (func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    ]