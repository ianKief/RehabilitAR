from sqlalchemy import or_, func, text
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from src.core.database import db

def alumno_tiene_asistencia (dni_alumno):

    query = (
        db.session.query(Reserva.asiste)
        .join(Alumno, Reserva.id_alumno == Alumno.id)
        .join(Clase, Reserva.id_clase == Clase.id)

        .filter(Usuario.dni == dni_alumno)
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
    if (estado != "seleccionar_todos"):
        filters.append(estado == reserva.asiste) # NOTA: estado es presente o ausente. Si se registra otra cosa ver
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
    )
    if cliente_filtrado:
        query.options(
            contains_eager(Reserva.id_alumno),
            selectinload(Comentario.id_reserva)
        )
    else: 
        query.options(
            joinedload(Reserva.id_alumno),
            selectinload(Comentario.id_reserva)
        )

    return db.session.scalars(query).all()

def subir_comentario (dni_alumno, comentario):

    id_reserva = (
        db.session.query(Reserva.id)
        .join (Cliente, Reserva.id_cliente == Cliente.id)
        .join (ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join (Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(dni_alumno == Usuario.dni)
        .filter(func.now() > Clase.fecha_hora)
        .filter(func.now() < (Clase.fecha_hora + (Clase.duracion * text("INTERVAL '1 minute'"))))
    )

    nuevo_comentario = Comentario(comentario=comentario, id_reserva = id_reserva)
    db.session.add(nuevo_comentario)
    db.session.commit()