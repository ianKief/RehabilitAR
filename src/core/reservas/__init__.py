from sqlalchemy import select, func
from sqlalchemy.orm import contains_eager
from src.core.database import db
from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.usuarios.usuarios import Usuario
from src.core.reservas.reservas import Reserva, AsistenciaReserva
from datetime import date, timedelta
import calendar

def listar_clases_disponibles_para_cliente(fecha=None, tipo=None, especialidad=None):
    """
    Retorna las clases disponibles (no suspendidas y aprobadas) con opciones de filtro
    para el calendario del cliente, orientadas a la toma de reservas.
    """
    query = select(Clase).filter(
        Clase.suspendida == False,
        Clase.aprobada == True,
        Clase.fecha_clase >= date.today()
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
        Clase.fecha_clase >= date.today()
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
    return db.session.get(Clase, id_clase)

def obtener_ids_clases_reservadas(id_cliente):
    """Obtiene una lista con los IDs de las clases en las que un cliente tiene una reserva activa (no cancelada)."""
    reservas = obtener_reservas_cliente(id_cliente)
    return [r.id_clase for r in reservas]

def obtener_reserva(id_cliente, id_clase):
    """Busca y retorna la reserva específica de un cliente para una clase determinada."""
    query = select(Reserva).filter_by(id_cliente=id_cliente, id_clase=id_clase)
    return db.session.scalars(query).first()

def reactivar_reserva(reserva):
    """Cambia el estado de una reserva previamente cancelada a 'ausente', volviéndola a activar."""
    reserva.asiste = AsistenciaReserva.AUSENTE
    db.session.commit()

def cancelar_reserva_core(reserva):
    """Cambia el estado de una reserva a 'cancelada', liberando el cupo."""
    reserva.asiste = AsistenciaReserva.CANCELADA
    db.session.commit()

def crear_reserva(id_cliente, id_clase):
    """Crea y registra una nueva reserva con estado 'ausente' para el cliente y la clase indicados."""
    nueva_reserva = Reserva(id_cliente=id_cliente, id_clase=id_clase, asiste=AsistenciaReserva.AUSENTE)
    db.session.add(nueva_reserva)
    db.session.commit()
    return nueva_reserva

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
        Clase.aprobada == True
    ).order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    
    return db.session.scalars(query).all()

def obtener_profesor_de_clase(id_clase):
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
        Clase.aprobada == True
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
    from src.core.usuarios import Cliente, Cola
    # Lo paso acá por importanción circular
    query = (db.session.query(Cola)
        .join (Cliente, Cliente.id == Cola.id_cliente)
        .join (Clase, Clase.id == Cola.id_clase)
        .filter (Cliente.id == id_cliente)
        .filter (Clase.id == id_clase)
        .filter (Cola.cancelada == False)
    )

    cola = db.session.scalars(query).one()

    if cola == None:
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
