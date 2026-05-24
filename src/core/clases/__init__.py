import calendar
from datetime import date, datetime, time, timedelta

from sqlalchemy import extract, select
from src.core.database import db
from src.core.clases.clases import Clase
from src.core.salas.salas import Sala, EstadoSala

def listar_clases():
    """Retorna todas las clases de rehabilitación ordenadas por fecha y hora."""
    query = select(Clase).order_by(
        Clase.fecha_clase.asc(), 
        Clase.horario.asc()
    )
    return db.session.scalars(query).all()

def obtener_clase_por_id(clase_id: int):
    """
    Busca una clase por su ID.
    Devuelve el objeto Clase si lo encuentra, o None si no existe.
    """
    # db.session.get es directo y eficiente para buscar por Clave Primaria
    clase = db.session.get(Clase, clase_id)
    return clase

def obtener_postulantes_clase(clase_id: int):
    """
    Retorna la lista de profesores postulados para una clase específica.
    (Por ahora mockeado, luego hará la consulta real a la tabla correspondiente)
    """
    # TODO: Reemplazar por la consulta real cuando tenga el modelo de profesores
    return [
        {"id": 101, "nombre": "Lic. Marcos Juárez", "especialidad": "Tren Inferior"},
        {"id": 102, "nombre": "Dra. Eliana Ribera", "especialidad": "Tren Medio"}
    ]

def obtener_sala_por_id(sala_id):
    """Busca una sala específica por su ID autoincremental."""
    return db.session.get(Sala, sala_id)

def listar_salas_habilitadas():
    """Retorna los objetos completos de las salas habilitadas (para sacar ID y Puerta en el HTML)."""
    query = select(Sala).filter(Sala.estado == EstadoSala.HABILITADA)
    return db.session.scalars(query).all()

def obtener_horarios_disponibles(fecha_evaluar, duracion_minutos=45, sala_id_evaluar=0, tipo_clase="Individual"):
    HORA_INICIO_LABORAL = 8
    HORA_FIN_LABORAL = 20
    INTERVALO_SLOTS = 30

    anio = fecha_evaluar.year
    mes = fecha_evaluar.month
    
    # Mapeo de día de la semana: Python (0=Lunes...6=Dom) a Postgres (0=Dom, 1=Lunes...6=Sáb)
    dia_semana_python = fecha_evaluar.weekday()
    dia_semana_postgres = (dia_semana_python + 1) % 7 

    if tipo_clase == "Fija":
        # Filtro optimizado en Postgres: solo trae las clases que coinciden en mes, año y día de la semana
        query = select(Clase).filter(
            extract('year', Clase.fecha_clase) == anio,
            extract('month', Clase.fecha_clase) == mes,
            extract('dow', Clase.fecha_clase) == dia_semana_postgres,
            Clase.sala_id == int(sala_id_evaluar),
            Clase.suspendida == False
        )
    else:
        query = select(Clase).filter(
            Clase.fecha_clase == fecha_evaluar,
            Clase.sala_id == int(sala_id_evaluar),
            Clase.suspendida == False
        )

    clases_del_dia = db.session.scalars(query).all()

    rangos_ocupados = []
    for c in clases_del_dia:
        inicio_dt = datetime.combine(fecha_evaluar, c.horario)
        fin_dt = inicio_dt + timedelta(minutes=c.duracion)
        rangos_ocupados.append((inicio_dt, fin_dt))

    horarios_libres = []
    enfoque_dt = datetime.combine(fecha_evaluar, time(HORA_INICIO_LABORAL, 0))
    fin_laboral_dt = datetime.combine(fecha_evaluar, time(HORA_FIN_LABORAL, 0))

    while enfoque_dt + timedelta(minutes=duracion_minutos) <= fin_laboral_dt:
        slot_inicio = enfoque_dt
        slot_fin = enfoque_dt + timedelta(minutes=duracion_minutos)

        superpuesto = False
        for inicio_ocu, fin_ocu in rangos_ocupados:
            if slot_inicio < fin_ocu and slot_fin > inicio_ocu:
                superpuesto = True
                break

        if not superpuesto:
            horarios_libres.append(slot_inicio.time().strftime('%H:%M'))

        enfoque_dt += timedelta(minutes=INTERVALO_SLOTS)

    return horarios_libres

def listar_especialidades_activas():
    """
    Simulación temporal de especialidades hasta que la tabla 
    esté creada e impactada en la base de datos.
    """
    # Creamos una estructura de datos falsa que simula tener los atributos .id y .nombre
    # Usamos diccionarios o un truco rápido con type de Python para simular objetos
    class EspecialidadSimulada:
        def __init__(self, id, nombre):
            self.id = id
            self.nombre = nombre

    especialidades= [
        EspecialidadSimulada(1, "Tren Inferior"),
        EspecialidadSimulada(2, "Tren Medio"),
        EspecialidadSimulada(3, "Tren Superior"),
        # Podés sumar las que quieras para probar cómo se ve el select
    ]
    
    return especialidades

def crear_clases_agenda(**datos_clase):
    """
    Se encarga de persistir las clases en la base de datos.
    Si es Fija, calcula los días restantes del mes y los inserta en bucle.
    """
    fecha_inicial = datos_clase['fecha_clase']
    tipo = datos_clase['tipo']
    
    fechas_a_procesar = []

    if tipo == "Fija":
        anio = fecha_inicial.year
        mes = fecha_inicial.month
        dia_semana_objetivo = fecha_inicial.weekday()
        hoy = date.today()

        # Obtenemos la matriz de semanas del mes correspondiente
        cal = calendar.monthcalendar(anio, mes)
        for semana in cal:
            dia = semana[dia_semana_objetivo]
            if dia != 0:
                fecha_calculada = date(anio, mes, dia)
                # CANDADO: Solo agregamos si es igual o posterior al día de hoy
                if fecha_calculada >= hoy:
                    fechas_for_loop = fecha_calculada
                    fechas_a_procesar.append(fechas_for_loop)
    else:
        fechas_a_procesar.append(fecha_inicial)

    # Si por el filtro de días pasados la lista quedó vacía, manejamos el caso
    if not fechas_a_procesar:
        return False

    # Guardamos cada registro de forma individual compartiendo los mismos parámetros
    for f in fechas_a_procesar:
        nueva_clase = Clase(
            nombre=datos_clase['nombre'],
            especialidad=datos_clase['especialidad'],
            duracion=datos_clase['duracion'],
            capacidad_maxima=datos_clase['capacidad_maxima'],
            descripcion=datos_clase['descripcion'],
            fecha_clase=f,  # Fecha específica del bucle
            horario=datos_clase['horario'],
            tipo=tipo,
            sala_id=datos_clase['sala_id'],
            suspendida=False,
            aprobada=True
        )
        db.session.add(nueva_clase)
    
    db.session.commit()
    return True