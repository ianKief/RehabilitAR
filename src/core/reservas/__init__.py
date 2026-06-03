from sqlalchemy import select, func, case, or_, and_
from sqlalchemy.orm import contains_eager

from src.core.database import db
from src.core.clases.clases import Clase, ProfesorDictaClase

from src.core.reservas.reservas import Reserva, AsistenciaReserva, Cola, Cancelacion
from datetime import date, timedelta, datetime
import calendar
from src.core.salas.salas import Sala
from src.core.functions import filtro_cliente_abonado
from flask_mail import Message
from src.core.mail import send_mail

def _filtro_clase_futura():
    ahora = datetime.now()
    return or_(
        Clase.fecha_clase > ahora.date(),
        and_(Clase.fecha_clase == ahora.date(), Clase.horario > ahora.time())
    )

def listar_clases_disponibles_para_cliente(fecha=None, tipo=None, especialidad=None):
    """
    Retorna las clases disponibles (no suspendidas y aprobadas) con opciones de filtro
    para el calendario del cliente, orientadas a la toma de reservas.
    """
    query = select(Clase).filter(
        Clase.suspendida == False,
        Clase.aprobada == True,
        _filtro_clase_futura()
    )
    
    if fecha:
        query = query.filter(Clase.fecha_clase == fecha)
    if tipo:
        query = query.filter(Clase.tipo.ilike(f"%{tipo}%"))
    if especialidad:
        query = query.filter(Clase.especialidad.ilike(f"%{especialidad}%"))
        
    query = query.order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    return db.session.scalars(query).all()

def obtener_fechas_con_clases(tipo=None, especialidad=None):
    """Retorna una lista de fechas (como strings YYYY-MM-DD) que tienen clases disponibles según los filtros."""
    query = select(Clase.fecha_clase).filter(
        Clase.suspendida == False,
        Clase.aprobada == True,
        _filtro_clase_futura()
    )
    
    if tipo:
        query = query.filter(Clase.tipo.ilike(f"%{tipo}%"))
    if especialidad:
        query = query.filter(Clase.especialidad.ilike(f"%{especialidad}%"))
        
    query = query.distinct().order_by(Clase.fecha_clase.asc())
    fechas = db.session.scalars(query).all()
    return [f.strftime("%Y-%m-%d") for f in fechas]

def obtener_clase_por_id(id_clase):
    """Obtiene un objeto Clase a partir de su identificador."""
    return db.session.scalars(db.session.query(Clase).filter(Clase.id==id_clase)).one_or_none()

def obtener_ids_clases_reservadas(id_cliente):
    """Obtiene una lista con los IDs de las clases en las que un cliente tiene una reserva activa (no cancelada)."""
    reservas = obtener_reservas_cliente(id_cliente)
    return [r.id_clase for r in reservas]

def obtener_ids_clases_encoladas(id_cliente):
    from src.core.usuarios.usuarios import Cliente
    """Obtiene una lista con los IDs de las clases en las que un cliente tiene una espera en cola activada (no cancelada)."""
    query = (db.session.query(Cola.id_clase)
        .join (Cliente, Cliente.id == Cola.id_cliente)
        .filter (Cliente.id == id_cliente)
        .filter (Cola.cancelada == False)
    )
    return db.session.scalars(query).all()

def obtener_reserva(id_cliente, id_clase):
    """Busca y retorna la reserva específica de un cliente para una clase determinada."""
    query = select(Reserva).filter_by(id_cliente=id_cliente, id_clase=id_clase).order_by(Reserva.fecha_modificacion.desc())
    return db.session.scalars(query).first()

def obtener_cola(id_cliente, id_clase):
    """Busca y retorna la cola específica de un cliente para una clase determinada."""
    query = (db.session.query(Cola)
        .filter(Cola.id_cliente == id_cliente)
        .filter(Cola.id_clase == id_clase)
        .filter(Cola.cancelada == False)
        .order_by(Cola.fecha_modificacion.desc())
    )
    return db.session.scalars(query).first()

def reactivar_reserva(reserva):
    """Cambia el estado de una reserva previamente cancelada a 'ausente', volviéndola a activar."""
    reserva.asiste = AsistenciaReserva.AUSENTE
    db.session.commit()

def cancelar_reserva_core(reserva):
    """Cambia el estado de una reserva a 'cancelada', liberando el cupo."""
    reserva.asiste = AsistenciaReserva.CANCELADA
    nueva_cancelacion = Cancelacion (
        descripcion = "El cliente ha cancelado la reserva",
        reserva = reserva,
        acredito_devolucion_previamente = False
    )
    db.session.add(nueva_cancelacion)
    if hay_cola (obtener_clase_por_id(reserva.id_clase)):
        dar_acceso_segun_orden_cola (reserva.id_clase)
    db.session.commit()

def cancelar_cola_core(cola):
    """Cambia el estado de una reserva a 'cancelada', liberando el cupo."""
    cola.cancelada = True
    db.session.commit()

def crear_reserva(id_cliente, id_clase):
    """Crea y registra una nueva reserva con estado 'ausente' para el cliente y la clase indicados."""
    nueva_reserva = Reserva(id_cliente=id_cliente, id_clase=id_clase, asiste=AsistenciaReserva.AUSENTE)
    db.session.add(nueva_reserva)
    db.session.commit()
    return nueva_reserva

def crear_espera_en_cola (id_cliente, id_clase):
    """Crea una nueva espera en la cola de espera"""
    nueva_cola = Cola (id_clase = id_clase, id_cliente = id_cliente, cancelada = False)
    db.session.add(nueva_cola)
    db.session.commit()
    return nueva_cola

def verificar_reserva_semanal_existente(id_cliente, fecha_clase):
    """Verifica si el cliente ya tiene una reserva activa para una clase de tipo 'Fija' en la misma semana."""
    start_of_week = fecha_clase - timedelta(days=fecha_clase.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    query = select(Reserva).join(Clase).filter(
        Reserva.id_cliente == id_cliente,
        Clase.tipo == "Fija",
        Clase.fecha_clase >= start_of_week,
        Clase.fecha_clase <= end_of_week,
        Reserva.asiste != AsistenciaReserva.CANCELADA
    )
    return db.session.scalars(query).first()

def verificar_limite_reservas_mensuales(id_cliente, clase_base):
    """Verifica si el cliente ya tiene una clase fija reservada en el mes que no coincida con el bloque actual."""
    if not clase_base:
        return False
        
    año = clase_base.fecha_clase.year
    mes = clase_base.fecha_clase.month
    
    fecha_inicio = date(año, mes, 1)
    _, dias_en_mes = calendar.monthrange(año, mes)
    fecha_fin = date(año, mes, dias_en_mes)

    query = select(Clase).join(Reserva).filter(
        Reserva.id_cliente == id_cliente,
        Clase.tipo == "Fija",
        Clase.fecha_clase >= fecha_inicio,
        Clase.fecha_clase <= fecha_fin,
        Reserva.asiste != AsistenciaReserva.CANCELADA
    )
    clases = db.session.scalars(query).all()
    
    bloque_actual = (clase_base.fecha_clase.weekday(), clase_base.horario, clase_base.nombre)
    
    for c in clases:
        b = (c.fecha_clase.weekday(), c.horario, c.nombre)
        # Si tiene una clase fija en el mes que no coincide con el bloque que intenta reservar,
        # chocaría con la regla de 1 clase fija por semana al hacer la reserva mensual completa.
        if b != bloque_actual:
            return True
            
    return False

def obtener_alternativas_semana_para_clase(clase_base):
    """Busca clases de la misma especialidad/nombre en la misma semana para reprogramar."""
    start_of_week = clase_base.fecha_clase - timedelta(days=clase_base.fecha_clase.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    query = select(Clase).filter(
        Clase.nombre == clase_base.nombre,
        Clase.tipo == clase_base.tipo,
        Clase.fecha_clase >= start_of_week,
        Clase.fecha_clase <= end_of_week,
        Clase.id != clase_base.id,
        Clase.suspendida == False,
        Clase.aprobada == True,
        _filtro_clase_futura()
    ).order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    
    return db.session.scalars(query).all()

def obtener_profesor_de_clase(id_clase):
    from src.core.usuarios.usuarios import Usuario
    """Devuelve el profesor asignado a una clase."""
    query = select(Usuario).join(
        ProfesorDictaClase, Usuario.id == ProfesorDictaClase.id_profesor
    ).filter(ProfesorDictaClase.id_clase == id_clase)
    return db.session.scalars(query).first()

def obtener_cupos_ocupados(id_clase):
    """Devuelve la cantidad de reservas activas para una clase."""
    query = select(func.count(Reserva.id)).filter(
        Reserva.id_clase == id_clase,
        Reserva.asiste != AsistenciaReserva.CANCELADA
    )
    return db.session.scalar(query) or 0

def obtener_clases_mensuales(id_clase_base):
    """Obtiene todas las clases del mismo mes, nombre, horario y día de la semana que la clase base proporcionada."""
    clase_base = obtener_clase_por_id(id_clase_base)
    if not clase_base:
        return []

    año = clase_base.fecha_clase.year
    mes = clase_base.fecha_clase.month
    dia_semana = clase_base.fecha_clase.weekday()

    _, dias_en_mes = calendar.monthrange(año, mes)
    fecha_inicio = date(año, mes, 1)
    fecha_fin = date(año, mes, dias_en_mes)

    query = select(Clase).filter(
        Clase.nombre == clase_base.nombre,
        Clase.horario == clase_base.horario,
        Clase.fecha_clase >= fecha_inicio,
        Clase.fecha_clase <= fecha_fin,
        Clase.tipo == "Fija",
        Clase.suspendida == False,
        Clase.aprobada == True,
        _filtro_clase_futura()
    )
    clases_mes = db.session.scalars(query).all()
    clases_mensuales = [c for c in clases_mes if c.fecha_clase.weekday() == dia_semana]
    clases_mensuales.sort(key=lambda x: x.fecha_clase)
    return clases_mensuales

def procesar_reservas_mensuales_automatica(id_cliente, clases_a_reservar):
    """Crea o reactiva de forma automática reservas para un cliente en un conjunto de clases mensuales iteradas."""
    reservas_creadas = 0
    for c in clases_a_reservar:
        reserva_exist = obtener_reserva(id_cliente, c.id)
        if reserva_exist and reserva_exist.asiste == AsistenciaReserva.CANCELADA:
            reserva_exist.asiste = AsistenciaReserva.AUSENTE
            reservas_creadas += 1
        elif not reserva_exist:
            nueva_reserva = Reserva(id_cliente=id_cliente, id_clase=c.id, asiste=AsistenciaReserva.AUSENTE)
            db.session.add(nueva_reserva)
            reservas_creadas += 1
    if reservas_creadas > 0:
        db.session.commit()
    return reservas_creadas

def cancelar_cola (id_cliente, id_clase):
    from src.core.usuarios.usuarios import Cliente
    """Cancela la cola, primero obteniéndola vía id_cliente y id_clase. Fuera de operación actualmente"""
    cola = obtener_cola(id_cliente, id_clase)
    if not cola:
        raise ValueError("No se ha podido encontrar la cola")
    
    cola.cancelada = True
    db.session.commit()

def obtener_reservas_cliente(id_cliente):
    """
    Retorna las reservas de un cliente específico, ordenadas por fecha y hora.
    """
    query = select(Reserva).join(Clase).options(
        contains_eager(Reserva.clase)
    ).filter(
        Reserva.id_cliente == id_cliente,
        Reserva.asiste != AsistenciaReserva.CANCELADA
    ).order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    
    return db.session.scalars(query).all()

def obtener_colas_cliente(id_cliente):
    """
    Retorna las esperas de un cliente específico, ordenadas por fecha y hora.
    """
    query = select(Cola).join(Clase).options(
        contains_eager(Cola.clase)
    ).filter(
        Cola.id_cliente == id_cliente,
        Cola.cancelada == False
    ).order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    
    return db.session.scalars(query).all()

def obtener_ids_clases_llenas_donde_el_cliente_no_tiene_reserva (id_cliente):
    """NOTA: puede estar en cola. Esa condición se comprueba con otra variante"""

    clases_donde_participa = (db.session.query(Reserva.id_clase)
        .filter(Reserva.id_cliente == id_cliente)
        .filter(Reserva.asiste != AsistenciaReserva.CANCELADA)
        .subquery()
    )

    query = (db.session.query(Clase.id)
    .join(Reserva, Reserva.id_clase == Clase.id)
    .join(Sala, Clase.sala_id == Sala.id)
    .group_by(Clase.id, Sala.capacidad)
    .having(
        func.sum(
            case(
                (Reserva.asiste != AsistenciaReserva.CANCELADA, 1),
                else_=0
            )
        ) >= Sala.capacidad
    )
    .filter(~Clase.id.in_(clases_donde_participa))
    )
    
    return db.session.scalars(query).all()

def devolver_cantidad_esperando_en_cola (clase):
    return (db.session.query(func.count(Cola.id))
        .filter(Cola.id_clase == clase.id)
        .filter(Cola.cancelada == False)
        .scalar()
    )

def hay_cola (clase):
    return devolver_cantidad_esperando_en_cola(clase) > 0

def dar_acceso_segun_orden_cola (id_clase):
    from src.core.usuarios.usuarios import Cliente
    clase = obtener_clase_por_id(id_clase)
    if not clase:
        raise ValueError("La clase no existe")
        
    try:
        query_base = (db.session.query(Cliente, Cola)
            .join(Cola, Cola.id_cliente == Cliente.id)
            .filter(Cola.cancelada == False, Cola.id_clase == id_clase)
            .order_by(Cola.fecha_modificacion.asc())
        )

        # Prioridad 1: Clientes abonados
        filtro_abonado = filtro_cliente_abonado(Cliente.id)
        if isinstance(filtro_abonado, (list, tuple)):
            datos = query_base.filter(*filtro_abonado).first()
        else:
            datos = query_base.filter(filtro_abonado).first()
        
        # Prioridad 2: Si no hay abonados, el primero en la cola general
        if not datos:
            datos = query_base.first()
            
        if not datos:
            raise ValueError("No hay clientes en cola")
        
        proximo, cola = datos
        cola.cancelada = True
        cola.en_reserva = True

        reserva_existente = obtener_reserva(proximo.id, id_clase)
        if reserva_existente:
            reserva_existente.asiste = AsistenciaReserva.AUSENTE
        else:
            nueva_reserva = Reserva(
                id_cliente=proximo.id,
                id_clase=id_clase,
                asiste=AsistenciaReserva.AUSENTE
            )
            db.session.add(nueva_reserva)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        raise e
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        raise ValueError("Ha habido un error con la base de datos") from e

    # Sección de enviado de mail
    try:
        body = f"Hola {proximo.nombre},\n\nSe le informa que la clase {clase.nombre} de la especialidad {clase.especialidad} ha generado una reserva para usted. En caso de no asistir informe su baja, caso contrario se le harán cargos."
        msg = Message(
            subject="RehabilitAR - Aviso de alta demanda",
            recipients=[proximo.email]
        )
        msg.body = body
        send_mail(msg)
    except Exception as e:
        print(f"No mandé el mail che: {e}")
        
    return proximo