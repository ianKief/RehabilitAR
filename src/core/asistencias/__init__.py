from sqlalchemy import or_, func, text, select, func
from sqlalchemy.orm import joinedload, selectinload, contains_eager, aliased
from src.core.database import db
from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reservas.reservas import Comentario, Reserva, AsistenciaReserva
from src.core.usuarios.usuarios import Usuario, RolUsuario, Cliente, Profesor

from src.core.functions import filtro_clase_actual

def alumno_tiene_asistencia (dni_alumno=None, id_alumno=None):
    """Devuelve True si el alumno tiene asistencia en la clase actual, False si no.
    Si no existe clase actual, devuleve None"""

    if dni_alumno != None:
        query = (
            db.session.query(Reserva.asiste)
            .join(Cliente, Reserva.id_cliente == Cliente.id)
            .join(Clase, Reserva.id_clase == Clase.id)

            .filter(Cliente.dni == dni_alumno)
            .filter(*filtro_clase_actual())
        )
    elif id_alumno != None:
        query = (
            db.session.query(Reserva.asiste)
            .join(Cliente, Reserva.id_cliente == Cliente.id)
            .join(Clase, Reserva.id_clase == Clase.id)

            .filter(Cliente.id == id_alumno)
            .filter(*filtro_clase_actual())
        )
    else:
        raise ValueError("registrar_presente_alumno necesita un parámetro de alumno (DNI o ID)")

    return db.session.scalars(query).one_or_none()

def conseguir_asistencias (id_profesor, busqueda="", estado='seleccionar_todos', fecha="", solo_comentarios=False):
    """Devuelve todas las asistencias basado en una serie de filtros. Si no encuentra nada, devuelve una lista vacía"""

    # Inicializaciones necesarias
    filters = []
    cliente_filtrado = False
 
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

    if solo_comentarios:
        reservas_faltantes_sin_comentarios = []
    else:
        reservas_faltantes_sin_comentarios = (
            db.session.query(Reserva.id)
            .join(Clase, Clase.id == Reserva.id_clase)
            .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
                        
            .filter(ProfesorDictaClase.id_profesor == id_profesor)
            .filter(Reserva.asiste == AsistenciaReserva.AUSENTE)
            .filter(*filtro_clase_actual())
            .filter(~Reserva.comentarios.any()) 
            
            .subquery()
        )
    
    # query en sí
    query = (
        db.session.query(Reserva)

        .join(Clase, Clase.id == Reserva.id_clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Cliente, Reserva.id_cliente == Cliente.id)

        .filter(ProfesorDictaClase.id_profesor == id_profesor)
        .filter(Reserva.asiste != AsistenciaReserva.CANCELADA)

        .filter(*filters)

        # filtramos los alumnos que no tienen comentarios y están ausentes, dado que son alumnos que aún no llegaron

        .filter(Reserva.id.notin_(reservas_faltantes_sin_comentarios))

        .order_by(Reserva.fecha_modificacion.desc())
    )

    if solo_comentarios:
        query = query.join(Comentario, Comentario.id_reserva == Reserva.id)
    else:
        query = query.outerjoin(Comentario, Comentario.id_reserva == Reserva.id)


    if cliente_filtrado:
        query = query.options(
            contains_eager(Reserva.cliente),
            contains_eager(Reserva.clase),
            selectinload(Reserva.comentarios)
        )
    else: 
        query = query.options(
            joinedload(Reserva.cliente),
            joinedload(Reserva.clase),
            selectinload(Reserva.comentarios)
        )

    return query.distinct().all()

def subir_comentario (dni_alumno, comentario):
    """Sube un comentario del alumno en la clase actual según su DNI.
    No tengo idea de qué sucede si no existe clase, aunque dado el contexto de su controller, no debería llegar hasta ese punto."""

    Profesor = aliased(Usuario)

    query = (
        db.session.query(Reserva.id)
        .join (Cliente, Reserva.id_cliente == Cliente.id)
        .join (Clase, Clase.id == Reserva.id_clase)
        .join (ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join (Profesor, ProfesorDictaClase.id_profesor == Profesor.id)

        .filter(dni_alumno == Cliente.dni)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(*filtro_clase_actual())
    )

    id_reserva = db.session.scalars(query).one()

    nuevo_comentario = Comentario(comentario = comentario, id_reserva = id_reserva)
    db.session.add(nuevo_comentario)
    db.session.commit()

def registrar_presente_alumno (dni_alumno=None, id_alumno=None):
    """Registra el presente de un alumno. En caso de que ya tenga el presente devuelve una excepción."""

    if dni_alumno != None:
        query = (
            db.session.query(Reserva)
            .join (Cliente, Cliente.id == Reserva.id_cliente)
            .join (Clase, Clase.id == Reserva.id_clase)

            .filter(Cliente.dni == dni_alumno)
            .filter(*filtro_clase_actual())
        )
    elif id_alumno != None:
        query = (
            db.session.query(Reserva)
            .join (Cliente, Cliente.id == Reserva.id_cliente)
            .join (Clase, Clase.id == Reserva.id_clase)

            .filter(Cliente.id == id_alumno)
            .filter(*filtro_clase_actual())
        )
    else:
        raise ValueError("registrar_presente_alumno necesita un parámetro de alumno (DNI o ID)")

    reserva_a_actualizar = db.session.scalars(query).one()
    if (reserva_a_actualizar.asiste != AsistenciaReserva.AUSENTE):
        print ("No deberíamos haber llegado acá.")
        raise ValueError("Ya se ha registrado el presente del alumno") # Esta condición debería comprobarse antes, por ende nunca debería llegarse acá
    reserva_a_actualizar.asiste = AsistenciaReserva.PRESENTE

    db.session.commit()
    return True

def finalizar_clase_y_penalizar(id_clase):
    """
    Cierra la clase: Marca como ausentes a todos los alumnos que no tengan presente,
    calcula su inasistencia histórica y bloquea a los que superen el 50%.
    """
    from src.core.usuarios import bloquear_usuario

    
    # 1. Buscamos todas las reservas de esta clase que NO sean PRESENTE ni CANCELADA
    # (Es decir, los que quedaron "colgados" o ya estaban por defecto en otro estado)
    query = (
        db.session.query(Reserva)
        .filter(Reserva.id_clase == id_clase)
        .filter(Reserva.asiste != AsistenciaReserva.PRESENTE)
        .filter(Reserva.asiste != AsistenciaReserva.CANCELADA)
    )
    
    reservas_sin_presente = query.all()
    
    ausentes_marcados = 0
    bloqueados = 0
    
    for reserva in reservas_sin_presente:
        # 2. Los marcamos como ausentes definitivamente
        reserva.asiste = AsistenciaReserva.AUSENTE
        ausentes_marcados += 1
        
        # 3. Calculamos el porcentaje histórico de inasistencias
        porcentaje_inasistencia, total_clases = calcular_porcentaje_inasistencia(reserva.id_cliente)
        
        if porcentaje_inasistencia >= 50 and total_clases >= 4:
            try:
                bloquear_usuario(reserva.id_cliente)
                bloqueados += 1
            except Exception as e:
                print(f"Error al bloquear al usuario {reserva.id_cliente}: {e}")
                
    db.session.commit()
    
    return ausentes_marcados, bloqueados

def calcular_porcentaje_inasistencia(id_cliente):
    """Calcula el porcentaje histórico de inasistencias de un cliente."""
    
    # 1. Obtenemos el total de clases (Presentes + Ausentes)
    stmt_total = (
        select(func.count(Reserva.id))
        .filter(Reserva.id_cliente == id_cliente)
        .filter(Reserva.asiste.in_([AsistenciaReserva.PRESENTE, AsistenciaReserva.AUSENTE]))
    )
    total_clases = db.session.execute(stmt_total).scalar()

    # Si nunca tuvo una clase completada, el porcentaje es 0
    if not total_clases or total_clases == 0:
        return 0.0

    # 2. Obtenemos el total de ausencias
    stmt_ausencias = (
        select(func.count(Reserva.id))
        .filter(Reserva.id_cliente == id_cliente)
        .filter(Reserva.asiste == AsistenciaReserva.AUSENTE)
    )
    total_ausencias = db.session.execute(stmt_ausencias).scalar()

    # 3. Calculamos el porcentaje
    return (total_ausencias / total_clases) * 100, total_clases

def buscar_clase_por_token (token):
    query = (db.session.query(Clase)
        .filter (Clase.token_qr == token)
    )
    return query.scalar()

def clase_sucediendo_actualmente_por_id (id_clase):
    query = (db.session.query(Clase)
        .filter(Clase.id == id_clase)
        .filter(*filtro_clase_actual())
    )
    return db.session.scalars(query).one_or_none