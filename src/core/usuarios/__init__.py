from sqlalchemy import func, text, or_
from src.core.database import db

def alumno_pertenece_a_clase_actual_profesor (id_profesor, dni_alumno):
    query = (
        db.session.query(Cliente.exists())
        .join(Reserva, Cliente.id == Reserva.id_cliente)
        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        .filter(Profesor.id == id_profesor)
        .filter(Usuario.dni == dni_alumno)
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    return db.session.scalars(query).all()

def conseguir_lista_alumnos_clase_actual (id_profesor, filtro_nombre = ""):
    # Inicializo el filtro de búsqueda
    filters = []
    busqueda = filtro_nombre.lower()
    if (busqueda != ""):
        filters.append(or_(Cliente.nombre.like(f"%{busqueda}%"), Cliente.apellido.like(f"%{busqueda}%"), Usuario.dni.like(f"%{busqueda}%")))

    # Preparo consulta
    query = (
        db.session.query(Cliente, func.avg(
            cast(Reserva.asiste, Integer)
        ).label("promedio_asistencia"))
        .join(Reserva, Reserva.id_cliente == Cliente.id)
        .join(Clase, Clase.id == Reserva,id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(Profesor.id == id_profesor)
        .filter(*filters)
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    return db.session.scalars(query).all()

def conseguir_perfil_alumno (dni_alumno):

    query = (
        db.session.query(Cliente)
        .filter(Cliente.dni == dni_alumno)
    )

    return db.session.scalars(query).one_or_none()

def tiene_alumnos (id_profesor, en_clase=False):
    filters= []
    if en_clase:
        filters.append(func.now() > Clase.fecha_hora)
        filters.append(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))

    query = (
        db.session.query(Alumno.exists())
        .join (Reserva, Alumno.id == Reserva.id_alumno)
        .join (Clase, Clase.id == Reserva.id_clase)
        .join (ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join (Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(Profesor.id == id_profesor)
        .filter(*filters)
    )

    return db.session.scalars(query).one()