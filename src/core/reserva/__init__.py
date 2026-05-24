from sqlalchemy import or_, func, text
from sqlalchemy.orm import joinedload, selectinload, contains_eager, aliased

from src.core.database import db

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reserva.reservas import Comentario, Reserva, AsistenciaReserva
from src.core.usuarios.usuarios import Usuario, RolUsuario

from src.core.functions import filtro_clase_actual

def alumno_tiene_asistencia (dni_alumno):
    """Devuelve True si el alumno tiene asistencia en la clase actual, False si no.
    Si no existe clase actual, devuleve None"""

    Cliente = aliased(Usuario)
    
    query = (
        db.session.query(Reserva.asiste)
        .join(Cliente, Reserva.id_cliente == Cliente.id)
        .join(Clase, Reserva.id_clase == Clase.id)

        .filter(Cliente.dni == dni_alumno)
        .filter(Cliente.rol == RolUsuario.CLIENTE)
        .filter(*filtro_clase_actual())
    )

    return db.session.scalars(query).one_or_none()

def conseguir_asistencias (id_profesor, busqueda="", estado='seleccionar_todos', fecha="", solo_comentarios=False):
    """Devuelve todas las asistencias basado en una serie de filtros. Si no encuentra nada, devuelve una lista vacía"""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    # Inicializaciones necesarias
    filters = []
    # LEER ABAJO: cliente_filtrado = False
 
    # Aplicando filtros al query
 
    if (busqueda != ""):
        cliente_filtrado = True
        filters.append(or_(Cliente.nombre.ilike(f"%{busqueda}%"), Cliente.apellido.ilike(f"%{busqueda}%"), Cliente.dni.ilike(f"%{busqueda}%"), Comentario.comentario.ilike(f"%{busqueda}%"), Clase.nombre.ilike(f"%{busqueda}%")))
        filters.append(Cliente.rol == RolUsuario.CLIENTE)
    # Nota: estado puede ser "seleccionar_todos", "presente" o "ausente"
    if (estado != "seleccionar_todos"):

        if (estado == "presente"):
            filters.append(Reserva.asiste == AsistenciaReserva.PRESENTE)
        else:
            filters.append(Reserva.asiste == AsistenciaReserva.AUSENTE)
    if (fecha != ""):
        filters.append(fecha == Clase.fecha_clase)

    # query en sí
    query = (
        db.session.query(Reserva, Cliente, Comentario, Clase)

        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        .join(Cliente, Reserva.id_cliente == Cliente.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(Reserva.asiste != AsistenciaReserva.CANCELADA)
        .filter(*filters)

        .order_by(Reserva.fecha_modificacion.desc())
    )

    if solo_comentarios:
        query = query.join(Comentario, Comentario.id_reserva == Reserva.id)
    else:
        query = query.outerjoin(Comentario, Comentario.id_reserva == Reserva.id)

    """Si en algún momento agregamos FKs y relationships, esta alternativa es la correcta y nos permitirá sacar la otra función en ver_asistencias.py

    if cliente_filtrado:
        query = query.options(
            contains_eager(Reserva.cliente),
            selectinload(Reserva.comentarios)
        )
    else: 
        query = query.options(
            joinedload(Reserva.cliente),
            selectinload(Reserva.comentarios)
        )
    """

    return query.all()
        

def subir_comentario (dni_alumno, comentario):
    """Sube un comentario del alumno en la clase actual según su DNI.
    No tengo idea de qué sucede si no existe clase, aunque dado el contexto de su controller, no debería llegar hasta ese punto."""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    query = (
        db.session.query(Reserva.id)
        .join (Cliente, Reserva.id_cliente == Cliente.id)
        .join (Clase, Clase.id == Reserva.id_clase)
        .join (ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join (Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(dni_alumno == Cliente.dni)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(Cliente.rol == RolUsuario.CLIENTE)
        .filter(*filtro_clase_actual())
    )

    id_reserva = db.session.scalars(query).one()

    nuevo_comentario = Comentario(comentario = comentario, id_reserva = id_reserva)
    db.session.add(nuevo_comentario)
    db.session.commit()

def registrar_presente_alumno (dni_alumno):
    """Registra el presente de un alumno. En caso de que ya tenga el presente devuelve una excepción."""

    Cliente = aliased(Usuario)

    query = (
        db.session.query(Reserva)
        .join (Cliente, Cliente.id == Reserva.id_cliente)
        .join (Clase, Clase.id == Reserva.id_clase)

        .filter(Cliente.dni == dni_alumno)
        .filter(Cliente.rol == RolUsuario.CLIENTE)
        .filter(*filtro_clase_actual())
    )

    reserva_a_actualizar = db.session.scalars(query).one()
    if (reserva_a_actualizar.asiste != AsistenciaReserva.AUSENTE):
        print ("No deberíamos haber llegado acá.")
        return False
    reserva_a_actualizar.asiste = AsistenciaReserva.PRESENTE

    db.session.commit()
    return True