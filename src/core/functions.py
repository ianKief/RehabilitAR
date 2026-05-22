from sqlalchemy import func, text, Date
from src.core.clases.clases import Clase

def filtro_clase_actual ():
    """Devuelve dos filtros para agarrar una clase actual. Para usar, hacer .filter(*filtro_clase_actual())"""
    return [
        (func.now().cast(Date) == Clase.fecha_clase)
        (func.now() > Clase.horario)
        (func.now() < (Clase.horario + (Clase.duracion * text("INTERVAL '1 minute'"))))
    ]