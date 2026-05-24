from sqlalchemy import or_, func, text
from sqlalchemy.orm import joinedload, selectinload, contains_eager, aliased

from src.core.database import db

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reserva.reservas import Comentario, Reserva, AsistenciaReserva
from src.core.usuarios.usuarios import Usuario, RolUsuario
from src.core.usuarios import bloquear_usuario

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

def finalizar_clase_y_penalizar(id_clase):
    """
    Cierra la clase: Marca como ausentes a todos los alumnos que no tengan presente,
    calcula su inasistencia histórica y bloquea a los que superen el 50%.
    """
    
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
        # TODO: Implementar la lógica real de cálculo de porcentaje
        # porcentaje_inasistencia = calcular_porcentaje_inasistencia(reserva.id_cliente)
        porcentaje_inasistencia = 0 # Temporal
        
        if porcentaje_inasistencia >= 50:
            try:
                bloquear_usuario(reserva.id_cliente)
                bloqueados += 1
            except Exception as e:
                print(f"Error al bloquear al usuario {reserva.id_cliente}: {e}")
                
    db.session.commit()
    
    return ausentes_marcados, bloqueados