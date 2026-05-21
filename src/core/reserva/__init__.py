from sqlalchemy import or_, func, text
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from src.core.database import db
from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reserva.reservas import Comentario, Reserva

def alumno_tiene_asistencia (dni_alumno):

    query = (
        db.session.query(Reserva.asiste)
        .join(Cliente, Reserva.id_cliente == Cliente.id)
        .join(Clase, Reserva.id_clase == Clase.id)

        .filter(Cliente.dni == dni_alumno)
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    return db.session.scalars(query).all()

def conseguir_asistencias (id_profesor, busqueda="", estado='seleccionar_todos', fecha="", solo_comentarios=False):
    # Inicializaciones necesarias
    filters = []
    joins = []
    cliente_filtrado = False

    # Aplicando filtros al query
    if (busqueda != ""):
        joins.append(Cliente, Reserva.id_cliente == Cliente.id)
        joins.append(Comentario, Comentario.id_reserva == Reserva.id)
        cliente_filtrado = True
        filters.append(or_(Cliente.nombre.like(f"%{busqueda}%"), Cliente.apellido.like(f"%{busqueda}%"), Cliente.dni.like(f"%{busqueda}%"), Comentario.comentario.like(f"%{busqueda}%")))
    # Nota: estado puede ser "seleccionar_todos", "presente" o "ausente". Reserva.asiste guarda True o False
    if (estado != "seleccionar_todos"):
        if (estado == "presente"):
            filters.append(True == reserva.asiste)
        else:
            filters.append(False == reserva.asiste)
    if (fecha != ""):
        filters.append(fecha == CLASE.fecha)
    if solo_comentarios == True:
        filters.append(Comentario.any())

    # query en sí
    query = (
        db.session.query(Reserva)
        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        .join(*joins)
        .filter(Profesor.id == id_profesor)
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

    query = (
        db.session.query(Reserva.id)
        .join (Cliente, Reserva.id_cliente == Cliente.id)
        .join (ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join (Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(dni_alumno == Cliente.dni)
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    id_reserva = db.session.scalars(query).one()

    nuevo_comentario = Comentario(comentario=comentario, id_reserva = id_reserva)
    db.session.add(nuevo_comentario)
    db.session.commit()

def registrar_presente_alumno (dni_alumno):

    # conseguir presente que marcar
    query = (
        db.session.query(Reserva)
        .join (Cliente, Cliente.id == Reserva.id_cliente)
        .join (Clase, Clase.id == Reserva.id_clase)

        .filter(dni_alumno == Cliente.dni)
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    reserva_a_actualizar = db.session.scalars(query).one()
    reserva_a_actualizar.asiste = True