from sqlalchemy import func, literal_column, Time
from src.core.clases.clases import Clase

def filtro_clase_actual ():
    """Devuelve dos filtros para filtrar que actualmente está sucediendo una clase. Para usar, hacer .filter(*filtro_clase_actual())"""
    
    hora_actual = devolver_hora_actual()

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

def devolver_hora_actual ():
    """Devuelve la hora actual como objeto sqlalchemy.Time.
    Recomendable usar en reemplazo de func.now() para evitar incongruencias horarias"""
    return func.timezone(
        'America/Argentina/Buenos_Aires',
        func.now()
    ).cast(Time)