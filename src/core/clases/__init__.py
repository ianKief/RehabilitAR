from sqlalchemy import select, text, func, case
from sqlalchemy.orm import aliased

from src.core.database import db

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reserva.reservas import Reserva
from src.core.usuarios.usuarios import Usuario

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
        ).label("reservas_totales"), func.sum(
            case(
                (Reserva.asiste, 1),
                else_=0
            )
        ).label("asistencias_actuales"), 0)

        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        # Las reglas de negocio no permiten que se de una clase sin alumnos, pero, dado el caso, outerjoin prepara el escenario
        .outerjoin(Reserva, Reserva.id_clase == Clase.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == "profesor")
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))

        .group_by(Clase.id)
    )

    return db.session.execute(query).one_or_none()

def profesor_está_en_clase (id_profesor):
    """Retorna un valor booleano que representa si el profesor está en clase"""

    Profesor = aliased(Usuario)

    query = (
        db.session.query(Clase.exists())
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == "profesor")
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    return db.session.scalars(query).one()
