from sqlalchemy import func, text, or_, select, cast, Integer, and_
from sqlalchemy.orm import aliased

from src.core.database import db

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reserva.reservas import Reserva
from src.core.usuarios.usuarios import Usuario, RolUsuario

from src.core.functions import filtro_clase_actual

def alumno_pertenece_a_clase_actual_profesor (id_profesor, dni_alumno):
    """Dado el ID del profesor y el DNI del alumno (que es el único dato que el profesor conoce de él), devuelve si el alumno pertenece a la clase actual del profesor"""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    query = (
        db.session.query(Cliente.exists())
        .join(Reserva, Cliente.id == Reserva.id_cliente)
        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(Profesor.id == id_profesor)
        .filter(Cliente.dni == dni_alumno)
        .filter(Profesor.rol == "profesor")
        .filter(Cliente.rol == "cliente")
        .filter(*filtro_clase_actual())
    )

    return db.session.scalars(query).one()

def conseguir_lista_alumnos_clase_actual (id_profesor, filtro_nombre = ""):
    """Dado un ID de profesor, consigue la lista de alumnos de la clase actual si lo hay.
    Con filtro_nombre="" se pueden filtrar los alumnos obtenidos"""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    # Inicializo el filtro de búsqueda
    filters = []
    if (filtro_nombre != ""):
        filters.append(or_(Cliente.nombre.like(f"%{filtro_nombre}%"), Cliente.apellido.like(f"%{filtro_nombre}%"), Cliente.dni.like(f"%{filtro_nombre}%")))

    # Preparo consulta
    query = (
        db.session.query(Cliente, func.avg(
            cast(Reserva.asiste, Integer), 0
        ).label("promedio_asistencia"))
        .join(Reserva, Reserva.id_cliente == Cliente.id)
        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == "profesor")
        .filter(Cliente.rol == "cliente")
        .filter(Reserva.asiste != "cancelada")
        .filter(*filters)
        .filter(*filtro_clase_actual())

        .group_by(Cliente.id)
        .order_by(Cliente.apellido, Cliente.nombre)
    )

    return db.session.execute(query).all()

def conseguir_perfil_alumno (dni_alumno):
    """Consigue el perfil del alumno con solo el DNI"""

    Cliente = aliased(Usuario)

    query = (
        db.session.query(Cliente)
        .filter(Cliente.dni == dni_alumno)
        .filter(Cliente.rol == "cliente")
    )

    return db.session.scalars(query).one_or_none()

def tiene_alumnos (id_profesor, en_clase_actual=False):
    """Devuelve True si tiene alumnos, False si no. Esto es en general, pero el parámetro en_clase_actual=False filtra (si está en True) si tiene alumnos en la clase actual (si la hay). False en caso contrario (no tira excepción)."""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    filters= []
    if en_clase_actual:
        filters.append(*filtro_clase_actual()) # Puede que haya que sacar el *

    query = (
        db.session.query(Cliente.exists())
        .join (Reserva, Cliente.id == Reserva.id_cliente)
        .join (Clase, Clase.id == Reserva.id_clase)
        .join (ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join (Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == "profesor")
        .filter(Cliente.rol == "cliente")
        .filter(*filters)
    )

    return db.session.scalars(query).one()

def listar_usuarios():
    """Devuelve una lista con todos los usuarios registrados."""
    stmt = select(Usuario).order_by(Usuario.id)
    return db.session.execute(stmt).scalars().all()

def crear_usuario(**kwargs):
    """Crea un nuevo usuario en la base de datos."""
    stmt = select(Usuario).filter_by(email=kwargs.get('email'))
    usuario_existente = db.session.execute(stmt).scalar_one_or_none()

    if usuario_existente:
        raise ValueError("El correo electrónico ya está registrado.")
    
    rol_str = kwargs.pop('rol')
    nuevo_usuario = Usuario(**kwargs, rol=RolUsuario(rol_str))
    db.session.add(nuevo_usuario)
    db.session.commit()
    return nuevo_usuario

def cliente_tiene_horario_disponible (clase):
    """Recibe una clase. Se fija el horario y se fija si hay alguna reserva no cancelada que coincida en dicho horario"""

    Cliente = aliased(Usuario)

    query = (
        db.session.query(Usuario.exists())
        .join (Reserva, Reserva.id_cliente == Cliente.id)
        .join (Clase, Clase.id == Reserva.id_clase)
        .filter(clase.fecha_clase == Clase.fecha_clase)
        .filter(or_(and_(clase.horario > Clase.fecha_hora), (clase.horario < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))), (and_(clase.horario + (clase.duracion * text("INTERVAL '1 minute'")) > Clase.fecha_hora), (clase.horario + (clase.duracion * text("INTERVAL '1 minute'")) < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))))
        # Protip: Ctrl + z activa salto de línea
    )

    return not db.session.scalars(query).one()

