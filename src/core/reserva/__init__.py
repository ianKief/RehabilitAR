

def alumno_tiene_asistencia (dni_alumno):

    query = (
        db.session.query(Reserva.asiste)
        .join(Alumno)
        .join(Usuario)
        .join(Clase)
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

def conseguir_asistencias (profesor_id, busqueda="", estado='seleccionar_todos', fecha="", solo_comentarios=False):
    filters = []
    joins = []
    cliente_filtrado = False

    if (busqueda != ""):
        joins.append(Cliente)
        joins.append(Usuario)
        cliente_filtrado = True
        filters.append(or_(Cliente.nombre.ilike(f"%{busqueda}%"), Cliente.apellido.ilike(f"%{busqueda}%"), Usuario.dni.ilike(f"%{busqueda}%"), Comentario.comentario.ilike(f"%{busqueda}%")))
    if (estado != "seleccionar_todos"):
        filters.append(estado == reserva.asiste) # NOTA: estado es presente o ausente. Si se registra otra cosa ver
    if (fecha != ""):
        joins.append(Clase)
        filters.append(fecha == CLASE.fecha)
    if solo_comentarios == True:
        filters.append(Comentario.any())

    query = (
        db.session.query(Reserva)
        .join(Clase)
        .join (Profesor)
        .join(*joins)
        .filter(Profesor.id == profesor_id)
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

    return bd.session.scalars(query).all()

def subir_comentario (dni_alumno, comentario):

    query = (
        db.session.query(Reserva.id)
        .join (Cliente)
        .join (Usuario)
        .join (Clase)
        .filter(dni_alumno == Usuario.dni)
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

    nuevo_comentario = Comentario(comentario=comentario, id_reserva = id_reserva)
    db.session.add(nuevo_comentario)
    db.session.commit()