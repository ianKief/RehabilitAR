from sqlalchemy import func, text, or_
from src.core.database import db

def alumno_pertenece_a_clase_actual_profesor (id_profesor, dni_alumno):
    query = (
        db.session.query(Cliente.exists())
        .join(Usuario)
        .join(Reserva)
        .join(Clase)
        .join (Profesor)
        .filter(Profesor.id == id_profesor)
        .filter(Usuario.dni == dni_alumno)
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

def conseguir_lista_alumnos_clase_actual (id_profesor, filtro_nombre = ""):
    filters = []
    busqueda = filtro_nombre.lower()
    if (busqueda != ""):
        filters.append(or_(Cliente.nombre.ilike(f"%{busqueda}%"), Cliente.apellido.ilike(f"%{busqueda}%"), Usuario.dni.ilike(f"%{busqueda}%")))

    query = (
        db.session.query(Cliente) # además devuelve un avg
        .join(Reserva)
        .join(Clase)
        .join (Profesor)
        .filter(Profesor.id == profesor_id)
        .filter(*filters)
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

def conseguir_lista_alumnos_por_id_profesor (id_profesor):

    query = (
        db.session.query(Cliente)
        .join(Reserva)
        .join(Clase)
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

def conseguir_nombre (dni):

    query = (
        db.session.query(Cliente.nombre, Cliente.apellido)
        .join(Usuario)
        .filter(Usuario.dni == dni)
    )

def conseguir_perfil_alumno (dni_alumno):

    query = (
        db.session.query(Cliente)
        .join(Usuario)
        .filter(Usuario.dni == dni_alumno)
    )

def tiene_alumnos (id_profesor):

    query = (
        db.session.query(Alumno.exists())
        .join (Reserva)
        .join (Clase)
        .join (Profesor)
        .filter(Profesor.id == id_profesor)
    )

def tiene_alumnos_en_clase (id_profesor):

    query = (
        db.session.query(Alumno.exists())
        .join (Reserva)
        .join (Clase)
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