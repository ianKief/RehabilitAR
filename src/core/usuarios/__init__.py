from sqlalchemy import func, text, or_, select, cast, Integer, and_, case
from sqlalchemy.orm import aliased

from src.core.database import db

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reserva.reservas import Reserva, AsistenciaReserva
from src.core.usuarios.usuarios import Usuario, RolUsuario

from src.core.functions import filtro_clase_actual

def alumno_pertenece_a_clase_actual_profesor (id_profesor, dni_alumno):
    """Dado el ID del profesor y el DNI del alumno (que es el único dato que el profesor conoce de él), devuelve si el alumno pertenece a la clase actual del profesor"""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    query = (
        db.session.query(Cliente)
        .join(Reserva, Cliente.id == Reserva.id_cliente)
        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(Profesor.id == id_profesor)
        .filter(Cliente.dni == dni_alumno)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(Cliente.rol == RolUsuario.CLIENTE)
        .filter(*filtro_clase_actual())
    )

    return db.session.query(
        query.exists()
    ).scalar()

def conseguir_lista_alumnos_clase_actual (id_profesor, filtro_nombre = None):
    """Dado un ID de profesor, consigue la lista de alumnos de la clase actual si lo hay.
    Con filtro_nombre="" se pueden filtrar los alumnos obtenidos"""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    # Inicializo el filtro de búsqueda
    filters = []

    if (filtro_nombre != None):
        filters.append(or_(Cliente.nombre.ilike(f"%{filtro_nombre}%"), Cliente.apellido.ilike(f"%{filtro_nombre}%"), Cliente.dni.ilike(f"%{filtro_nombre}%")))

    # Preparo consulta
    query = (
        db.session.query(Cliente)
        .join(Reserva, Reserva.id_cliente == Cliente.id)
        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(Cliente.rol == RolUsuario.CLIENTE)
        .filter(Reserva.asiste != AsistenciaReserva.CANCELADA)
        .filter(*filters)
        .filter(*filtro_clase_actual())

        .order_by(Cliente.apellido, Cliente.nombre)
    )

    return db.session.scalars(query).all()

def conseguir_perfil_alumno (dni_alumno):
    """Consigue el perfil del alumno con solo el DNI"""

    Cliente = aliased(Usuario)

    query = (
        db.session.query(Cliente, func.avg(
            case (
                (Reserva.asiste == AsistenciaReserva.PRESENTE, 1),
                else_=0
            )).label("promedio_asistencia"))
        .join(Reserva, Reserva.id_cliente == Cliente.id)
        .filter(Cliente.dni == dni_alumno)
        .filter(Cliente.rol == RolUsuario.CLIENTE)
        .group_by(Cliente.id)
    )

    return query.one_or_none()

def tiene_alumnos (id_profesor, en_clase_actual=False):
    """Devuelve True si tiene alumnos, False si no. Esto es en general, pero el parámetro en_clase_actual=False filtra (si está en True) si tiene alumnos en la clase actual (si la hay). False en caso contrario (no tira excepción)."""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    filters= []
    if en_clase_actual:
        filters.extend(filtro_clase_actual())

    query = (
        db.session.query(Cliente)
        .join (Reserva, Cliente.id == Reserva.id_cliente)
        .join (Clase, Clase.id == Reserva.id_clase)
        .join (ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join (Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(Cliente.rol == RolUsuario.CLIENTE)
        .filter(*filters)
    )

    return db.session.query(
        query.exists()
    ).scalar()

def obtener_usuario_por_id_core(user_id):
    """Devuelve un usuario dado su ID."""
    return db.session.get(Usuario, user_id)

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