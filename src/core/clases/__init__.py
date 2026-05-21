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

def obtener_clase_por_id(clase_id: int):
    """
    Busca una clase por su ID.
    Devuelve el objeto Clase si lo encuentra, o None si no existe.
    """
    # db.session.get es directo y eficiente para buscar por Clave Primaria
    clase = db.session.get(Clase, clase_id)
    return clase

def obtener_postulantes_clase(clase_id: int):
    """
    Retorna la lista de profesores postulados para una clase específica.
    (Por ahora mockeado, luego hará la consulta real a la tabla correspondiente)
    """
    # TODO: Reemplazar por la consulta real cuando tenga el modelo de profesores
    return [
        {"id": 101, "nombre": "Lic. Marcos Juárez", "especialidad": "Tren Inferior"},
        {"id": 102, "nombre": "Dra. Eliana Ribera", "especialidad": "Tren Medio"}
    ]