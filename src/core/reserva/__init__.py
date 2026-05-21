from sqlalchemy import or_, func, text
from sqlalchemy.orm import joinedload, selectinload, contains_eager, aliased

from src.core.database import db

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reserva.reservas import Comentario, Reserva
from src.core.usuarios.usuarios import Usuario

def alumno_tiene_asistencia (dni_alumno):
    """Devuelve True si el alumno tiene asistencia en la clase actual, False si no.
    Si no existe clase actual, devuleve None"""

    Cliente = aliased(Usuario)
    
    query = (
        db.session.query(Reserva.asiste)
        .join(Cliente, Reserva.id_cliente == Cliente.id)
        .join(Clase, Reserva.id_clase == Clase.id)

        .filter(Cliente.dni == dni_alumno)
        .filter(Cliente.rol == "cliente")
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    return db.session.scalars(query).one_or_none()

def conseguir_asistencias (id_profesor, busqueda="", estado='seleccionar_todos', fecha="", solo_comentarios=False):
    """Devuelve todas las asistencias basado en una serie de filtros. Si no encuentra nada, devuelve una lista vacía"""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    # Inicializaciones necesarias
    filters = []
    cliente_filtrado = False

    # Aplicando filtros al query
    if (busqueda != ""):
        cliente_filtrado = True
        filters.append(or_(Cliente.nombre.like(f"%{busqueda}%"), Cliente.apellido.like(f"%{busqueda}%"), Cliente.dni.like(f"%{busqueda}%"), Comentario.comentario.like(f"%{busqueda}%")))
        filters.append(Cliente.rol == "cliente")
    # Nota: estado puede ser "seleccionar_todos", "presente" o "ausente". Reserva.asiste guarda True o False
    if (estado != "seleccionar_todos"):
        if (estado == "presente"):
            filters.append(True == Reserva.asiste)
        else:
            filters.append(False == Reserva.asiste)
    if (fecha != ""):
        filters.append(fecha == Clase.fecha)
    if solo_comentarios == True:
        filters.append(Comentario.any())

    # query en sí
    query = (
        db.session.query(Reserva)
        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        .join(Cliente, Reserva.id_cliente == Cliente.id)
        .outerjoin(Comentario, Comentario.id_reserva == Reserva.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == "profesor")
        .filter(*filters)
        .order_by(Reserva.fecha_modificacion.desc())
    )
    if cliente_filtrado:
        query.options(
            contains_eager(Reserva.id_cliente),
            selectinload(Comentario.id_reserva)
        )
    else: 
        query.options(
            joinedload(Reserva.id_cliente),
            selectinload(Comentario.id_reserva)
        )

    return db.session.scalars(query).all()

def subir_comentario (dni_alumno, comentario):
    """Sube un comentario del alumno en la clase actual según su DNI.
    No tengo idea de qué sucede si no existe clase, aunque dado el contexto de su controller, no debería llegar hasta ese punto."""

    Profesor = aliased(Usuario)
    Cliente = aliased(Usuario)

    query = (
        db.session.query(Reserva.id)
        .join (Cliente, Reserva.id_cliente == Cliente.id)
        .join (Clase, Clase.id, Reserva.id_clase)
        .join (ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join (Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(dni_alumno == Cliente.dni)
        .filter(Profesor.rol == "profesor")
        .filter(Cliente.rol == "cliente")
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
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

        .filter(dni_alumno == Cliente.dni)
        .filter(Cliente.rol == "cliente")
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    reserva_a_actualizar = db.session.scalars(query).one()
    if (reserva_a_actualizar.asiste == True):
        print ("No deberíamos haber llegado acá. Méteme una excepción :P")
        return
    reserva_a_actualizar.asiste = True