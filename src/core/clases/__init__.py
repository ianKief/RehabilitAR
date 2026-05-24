from sqlalchemy import select, text, func, case
from sqlalchemy.orm import aliased

from src.core.database import db

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reserva.reservas import Reserva, AsistenciaReserva
from src.core.usuarios.usuarios import Usuario, RolUsuario

from src.core.functions import filtro_clase_actual

def listar_clases():
    """Retorna todas las clases de rehabilitación ordenadas por fecha y hora."""
    query = select(Clase).order_by(
        Clase.fecha_clase.asc(), 
        Clase.horario.asc()
    )
    return db.session.scalars(query).all()

def conseguir_clase_actual (id_profesor):
    """Retorna la clase actual del profesor o None. profesor/index.html maneja None de manera adaptativa"""

    Profesor = aliased(Usuario)
    
    query = (
        db.session.query(Clase, func.count(
            Reserva.id
        ).label("reservas_totales"), func.coalesce(
            func.sum(case(
                (Reserva.asiste == AsistenciaReserva.PRESENTE, 1),
                else_=0
            )), 0
        ).label("asistencias_actuales"))

        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        # Las reglas de negocio no permiten que se de una clase sin alumnos, pero, dado el caso, outerjoin prepara el escenario
        .outerjoin(Reserva, Reserva.id_clase == Clase.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(*filtro_clase_actual())

        .group_by(Clase.id)
    )

    return db.session.execute(query).one_or_none()

def profesor_está_en_clase (id_profesor):
    """Retorna un valor booleano que representa si el profesor está en clase"""

    Profesor = aliased(Usuario)

    query = (
        db.session.query(Clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(*filtro_clase_actual())
    )

    return db.session.query(
        query.exists()
    ).scalar()

def clase_tiene_lugar(clase):

    cantidad_lugares_ocupados = (
        db.session.query(func.count(Reserva.id))
        .filter(Reserva.id_clase == clase.id)
        .filter(Reserva.asiste != AsistenciaReserva.CANCELADA)
    )

    ocupados = (db.session.scalar(cantidad_lugares_ocupados) or 0)

    return ocupados < clase.capacidad_maxima

