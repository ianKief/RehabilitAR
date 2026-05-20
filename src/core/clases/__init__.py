from sqlalchemy import select
from src.core.database import db
from src.core.clases.clases import Clase

def listar_clases():
    """Retorna todas las clases de rehabilitación ordenadas por fecha y hora."""
    query = select(Clase).order_by(
        Clase.fecha_clase.asc(), 
        Clase.horario.asc()
    )
    return db.session.scalars(query).all()

def conseguir_clase_actual (id_profesor):
    """Retorna la clase actual del profesor o una excepción si no hay ninguna"""
    query = (
        db.session.query(Clase)
        .join (Profesor)
        .filter(Profesor.id == id_profesor)
        .filter(func.now() > Clase.fecha_hora)
        .filter(
            func.now() <
            (
                Clase.fecha_hora +
                (
                    Clase.duracion *
                    text("INTERVAL '1 minute'")
                )
            )
        )
    )
    # comprobar si es null, tirar excepción si eso (o usar la función de antes previamente :P)

def profesor_está_en_clase (dni_profesor):
    """Retorna un valor booleano que representa si el profesor está en clase"""
    query = (
        db.session.query(Clase.exists())
        .join (Profesor)
        .filter(Profesor.id == id_profesor)
        .filter(func.now() > Clase.fecha_hora)
        .filter(
            func.now() <
            (
                Clase.fecha_hora +
                (
                    Clase.duracion *
                    text("INTERVAL '1 minute'")
                )
            )
        )
    )
