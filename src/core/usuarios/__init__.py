from sqlalchemy import func, text, or_, select, cast, Integer, and_, case
from sqlalchemy.orm import aliased

from flask_mail import Message

from src.core.database import db
from src.core.usuarios.usuarios import Usuario, RolUsuario, EstadoUsuario

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reservas.reservas import Reserva, AsistenciaReserva
from src.core.usuarios.usuarios import Usuario, Cliente, Profesor, Administrador, Recepcionista, RolUsuario

from src.core.functions import filtro_clase_actual
from datetime import datetime

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

def listar_usuarios(nombre=None, apellido=None, dni=None, email=None, rol=None, estado=None):
    """Devuelve una lista con todos los usuarios registrados.
    Si hay parametros, los filtra."""
    stmt = select(Usuario).order_by(Usuario.id)
    if nombre:
        stmt = stmt.where(Usuario.nombre == nombre)
    if apellido:
        stmt = stmt.where(Usuario.apellido == apellido)
    if dni:
        stmt = stmt.where(Usuario.dni == dni)
    if email:
        stmt = stmt.where(Usuario.email == email)
    if rol:
        stmt = stmt.where(Usuario.rol == RolUsuario(rol))
    if estado:
        stmt = stmt.where(Usuario.estado == EstadoUsuario(estado))
        
    return db.session.execute(stmt).scalars().all()

def crear_usuario(**kwargs):
    """Crea un nuevo usuario en la base de datos."""
    stmt = select(Usuario).filter_by(email=kwargs.get('email'))
    usuario_existente = db.session.execute(stmt).scalar_one_or_none()

    if usuario_existente:
        raise ValueError("El correo electrónico ya está registrado.")
    
    rol_str = kwargs.pop('rol')
    rol_enum = RolUsuario(rol_str)
    clases_por_rol = {
        RolUsuario.CLIENTE: Cliente,
        RolUsuario.PROFESOR: Profesor,
        RolUsuario.ADMINISTRADOR: Administrador,
        RolUsuario.RECEPCIONISTA: Recepcionista
    }
    clase_elegida = clases_por_rol.get(rol_enum)
    if not clase_elegida:
        raise ValueError("Rol no válido.")
    nuevo_usuario = clase_elegida(rol=rol_enum, **kwargs)
    db.session.add(nuevo_usuario)
    db.session.commit()
    return nuevo_usuario

def actualizar_rol_usuario(usuario_id, nuevo_rol):
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        raise ValueError("El usuario no existe.")

    usuario.rol = RolUsuario(nuevo_rol)
    db.session.commit()
    return usuario

def bloquear_usuario(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        raise ValueError("El usuario no existe.")
        
    usuario.estado = EstadoUsuario.BLOQUEADO
    db.session.commit()
    return usuario

def habilitar_usuario(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        raise ValueError("El usuario no existe.")
        
    # REGLA DE NEGOCIO: Verificar que no tenga deudas pendientes.
    # Cuando se implemente el módulo de pagos se reemplaza "False" por la función real.
    # Ejemplo: tiene_deuda = verificar_deuda_core(usuario_id)
    tiene_deuda = False 
    
    if tiene_deuda:
        raise ValueError("Actualización fallida: El usuario posee deudas pendientes")
        
    usuario.estado = EstadoUsuario.ACTIVO
    db.session.commit()
    return usuario

def eliminar_usuario(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        raise ValueError("El usuario no existe.")
        
    db.session.delete(usuario)
    db.session.commit()
    return True

def tiene_apto_fisico_valido(cliente):
    """Valida si el cliente tiene un apto físico aceptado y menor a 1 año de antigüedad."""
    if cliente and getattr(cliente, 'apto_fisico', None) and cliente.apto_fisico.estado.name == 'ACEPTADO':
        if cliente.apto_fisico.fecha_carga and (datetime.now() - cliente.apto_fisico.fecha_carga).days <= 365:
            return True
    return False

def conseguir_administrativos ():
    return db.session.scalars(db.session.query(Administrador)).all()

def informar_alta_demanda (clase):
    from src.web import mail
    try:
        administrativos = conseguir_administrativos ()
        for admin in administrativos:
            body = f"""Hola {admin.nombre},

                    Se le informa que la clase {clase.nombre} de la especialidad {clase.especialidad} está teniendo picos de demanda, habiendo superado recientemente las 10 esperas en cola.
                    Se le aconseja considerar más clases de este estilo para un futuro."""
            msg = Message(
                        subject="RehabilitAR - Aviso de alta demanda",
                        recipients=[admin.email]
                    )
            msg.body = body
            mail.send(msg)
    except ValueError as e:
        clase.aviso_alta_demanda = False
# Tampoco voy a informar al cliente del problema, mejor guardar el aviso para una próxima ocasión
