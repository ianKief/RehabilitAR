from sqlalchemy import func, text, Date, literal_column, Time
from src.core.clases.clases import Clase

def filtro_clase_actual ():
    """Devuelve dos filtros para filtrar que actualmente está sucediendo una clase. Para usar, hacer .filter(*filtro_clase_actual())"""
    
    hora_actual = func.timezone(
        'America/Argentina/Buenos_Aires',
        func.now()
    ).cast(Time)

    return [

        func.current_date() == Clase.fecha_clase,

        hora_actual > Clase.horario,

        hora_actual < (
            Clase.horario
            +
            (
                Clase.duracion
                * literal_column(
                    "INTERVAL '1 minute'"
                )
            )
        )
    ]