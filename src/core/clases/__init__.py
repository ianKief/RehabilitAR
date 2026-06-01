import calendar
from datetime import date, datetime, time, timedelta
from sqlalchemy import select, text, func, case
from sqlalchemy.orm import aliased

from src.core.database import db

from src.core.clases.clases import Clase, ProfesorDictaClase
from src.core.reservas.reservas import Reserva, AsistenciaReserva
from src.core.usuarios.usuarios import Usuario, RolUsuario
from src.core.reservas import devolver_cantidad_esperando_en_cola

from src.core.functions import filtro_clase_actual

from sqlalchemy import and_, extract, func, select
from src.core.usuarios.usuarios import Especialidad, Profesor, Usuario

from src.core.database import db
from src.core.clases.clases import Clase, ClaseBloque, PostulacionClase, ProfesorDictaClase
from src.core.salas.salas import Sala, EstadoSala
from src.core.usuarios.usuarios import tz_arg

# <VER CLASES ADMIN>
def listar_clases():
    """Retorna todas las clases de rehabilitación ordenadas por fecha y hora."""
    query = select(Clase).order_by(
        Clase.fecha_clase.asc(), 
        Clase.horario.asc()
    )
    return db.session.scalars(query).all()
# <VER CLASES ADMIN/>

# <DETALLE DE CLASE>
def obtener_clase_por_id(clase_id: int):
    """
    Busca una clase por su ID.
    Devuelve el objeto Clase si lo encuentra, o None si no existe.
    """
    clase = db.session.get(Clase, clase_id)
    return clase

def obtener_postulantes_clase(clase_id: int):
    """
    Retorna los postulantes de una clase y la información del profesor asignado si existiese.
    Adaptado a la herencia polimórfica y Enums del nuevo esquema.
    """
    # 1. 🔍 VERIFICAR SI ALGUIEN YA DICTA ESTA CLASE ACTUALMENTE
    query_asignado = (
        select(
            Usuario.nombre,
            Usuario.apellido,
            Especialidad.nombre.label("especialidad_enum") # Traemos el objeto Enum
        )
        .join(ProfesorDictaClase, ProfesorDictaClase.id_profesor == Usuario.id)
        # SQLAlchemy une automáticamente Usuario y Profesor por su herencia (id == id)
        .join(Profesor) 
        # 🔄 CAMBIO: especialidad_id -> id_especialidad
        .join(Especialidad, Profesor.id_especialidad == Especialidad.id)
        .filter(ProfesorDictaClase.id_clase == clase_id)
    )
    res_asignado = db.session.execute(query_asignado).first()
    
    profesor_asignado = None
    if res_asignado:
        profesor_asignado = {
            "nombre_completo": f"{res_asignado.nombre} {res_asignado.apellido}",
            # 🔄 CAMBIO: Extraemos el String (.value) para que la interfaz muestre "TREN SUPERIOR"
            "especialidad": res_asignado.especialidad_enum.value if res_asignado.especialidad_enum else "N/A"
        }

    # 2. 📑 TRAER LA LISTA DE POSTULACIONES
    query_postulantes = (
        select(
            PostulacionClase.id.label("postulacion_id"),
            PostulacionClase.estado.label("estado"),
            Usuario.nombre.label("nombre_profesor"),
            Usuario.apellido.label("apellido_profesor"),
            Especialidad.nombre.label("especialidad_enum")
        )
        .join(Usuario, PostulacionClase.profesor_id == Usuario.id)
        .join(Profesor)

        .join(Especialidad, Profesor.id_especialidad == Especialidad.id)
        .filter(PostulacionClase.clase_id == clase_id)
    )
    resultados = db.session.execute(query_postulantes).all()
    
    postulantes_limpios = []
    for r in resultados:
        postulantes_limpios.append({
            "id_postulacion": r.postulacion_id,
            "estado": r.estado,  # 'PENDIENTE', 'ACEPTADA', 'RECHAZADA'
            "nombre_completo": f"{r.nombre_profesor} {r.apellido_profesor}",
            # 🔄 CAMBIO: Usamos .value para limpiar el Enum y enviar solo el texto
            "especialidad": r.especialidad_enum.value if r.especialidad_enum else "N/A"
        })
        
    return {
        "postulantes": postulantes_limpios,
        "asignado": profesor_asignado
    }
# <DETALLE DE CLASE/>

# <CREAR CLASE>
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
    Retorna la lista real de especialidades ordenadas alfabéticamente
    directo desde la base de datos.
    """
    # Ordenamos usando el valor en texto del Enum
    query = select(Especialidad).order_by(Especialidad.nombre.asc())
    especialidades = db.session.scalars(query).all()
    return especialidades

def crear_clases_agenda(**datos_clase):
    """
    Se encarga de persistir las clases en la base de datos.
    Si es Fija, calcula los días restantes del mes, genera un id_bloque único
    y los vincula de forma atómica en la tabla intermedia.
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
                # CANDADO: Solo agrega si es igual o posterior al día de hoy
                if fecha_calculada > hoy:
                    fechas_a_procesar.append(fecha_calculada)
    else:
        fechas_a_procesar.append(fecha_inicial)

    if not fechas_a_procesar:
        return False

    # SI ES FIJA: Calculamos de antemano el próximo id_bloque secuencial libre
    id_bloque_actual = None
    if tipo == "Fija":
        max_bloque = db.session.scalar(select(func.max(ClaseBloque.id_bloque)))
        id_bloque_actual = (max_bloque + 1) if max_bloque is not None else 1

    try:
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
            
            # SI ES FIJA: Acoplamos la clase recién creada al bloque
            if tipo == "Fija":
                # Forzamos la asignación del ID en Postgres para esta iteración
                db.session.flush()
                
                asociacion_bloque = ClaseBloque(
                    id_bloque=id_bloque_actual,
                    id_clase=nueva_clase.id
                )
                db.session.add(asociacion_bloque)

        # Si todo salió bien en el bucle, confirmamos la transacción entera
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error crítico en el Core al persistir la agenda: {e}")
        return False
# <CREAR CLASE/>

# <POSTULACION DE PROFESORES>
def obtener_clases_disponibles_para_profesor(profesor_id):
    hoy = date.today()

    # 1. 🔍 BUSCAMOS LA ESPECIALIDAD DEL PROFESOR
    query_especialidad = (
        select(Especialidad.nombre)
        .join(Profesor, Profesor.id_especialidad == Especialidad.id)
        .filter(Profesor.id == profesor_id)
    )
    nombre_especialidad = db.session.execute(query_especialidad).scalar_one_or_none()

    if not nombre_especialidad:
        return []

    # Subquery: Clases que ya tienen dueño
    clases_ocupadas_subquery = select(ProfesorDictaClase.id_clase)

    # 2. 📑 QUERY BASE DE CLASES DISPONIBLES
    query = (
        select(Clase)
        .outerjoin(
            PostulacionClase,
            and_(
                PostulacionClase.clase_id == Clase.id,
                PostulacionClase.profesor_id == profesor_id
            )
        )
        .filter(
            Clase.fecha_clase > hoy,
            Clase.suspendida == False,
            func.upper(Clase.especialidad) == nombre_especialidad.value,
            Clase.id.not_in(clases_ocupadas_subquery),
            PostulacionClase.id == None
        )
        .order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    )
    clases_sueltas = db.session.scalars(query).all()

    # 3.MAPEO DE BLOQUES (Para agrupar las fijas de forma real)
    ids_clases = [c.id for c in clases_sueltas]
    clase_a_bloque = {}
    
    if ids_clases:
        query_bloques = select(ClaseBloque).filter(ClaseBloque.id_clase.in_(ids_clases))
        registros_bloques = db.session.scalars(query_bloques).all()
        clase_a_bloque = {rb.id_clase: rb.id_bloque for rb in registros_bloques}

    clases_agrupadas = {}

    for clase in clases_sueltas:
        if clase.tipo == "Fija" and clase.id in clase_a_bloque:
            clave = f"BLOQUE_{clase_a_bloque[clase.id]}"
        else:
            clave = f"INDIVIDUAL_{clase.id}"
        
        if clave not in clases_agrupadas:
            clases_agrupadas[clave] = {
                "objeto_base": clase,
                "fechas": [],
                "ids_clases": []
            }
            
        clases_agrupadas[clave]["fechas"].append(clase.fecha_clase)
        clases_agrupadas[clave]["ids_clases"].append(clase.id)

    return list(clases_agrupadas.values())

def obtener_postulaciones_de_profesor(profesor_id):
    """
    Trae el listado de postulaciones hechas por un profesor, agrupadas de forma 
    real según pertenezcan a un bloque recurrente o sean individuales.
    """
    # QUERY BASE 
    query = (
        select(PostulacionClase)
        .join(Clase, PostulacionClase.clase_id == Clase.id)
        .filter(PostulacionClase.profesor_id == profesor_id)
        .order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    )
    postulaciones_sueltas = db.session.scalars(query).all()

    # MAPEO DE BLOQUES DE LA BD
    # Extraemos todas las clases involucradas en las postulaciones encontradas
    ids_clases = [postu.clase_id for postu in postulaciones_sueltas]
    clase_a_bloque = {}
    
    if ids_clases:
        query_bloques = select(ClaseBloque).filter(ClaseBloque.id_clase.in_(ids_clases))
        registros_bloques = db.session.scalars(query_bloques).all()
        # Mapeamos { id_clase: id_bloque } para resolver rápido en el bucle
        clase_a_bloque = {rb.id_clase: rb.id_bloque for rb in registros_bloques}

    bloques_postulados = {}

    # AGRUPACIÓN LIMPIA POR BLOQUE O CLASE INDIVIDUAL
    for postu in postulaciones_sueltas:
        clase = postu.clase  # Mantiene la relación mapeada del modelo
        
        # Determinamos la clave única basada en datos reales de la BD
        if clase.tipo == "Fija" and clase.id in clase_a_bloque:
            clave = f"BLOQUE_{clase_a_bloque[clase.id]}"
        else:
            clave = f"INDIVIDUAL_{postu.id}"
            
        if clave not in bloques_postulados:
            bloques_postulados[clave] = {
                "clase_base": clase,
                "estado": postu.estado,  
                "fechas": [],
                "fecha_postulacion": postu.fecha_registro
            }
            
        # Acumulamos la fecha de esta instancia en particular
        bloques_postulados[clave]["fechas"].append(clase.fecha_clase)

    return list(bloques_postulados.values())

def obtener_clases_dictadas_por_profesor(profesor_id: int):
    """
    Trae las clases asignadas a un profesor que aún no sucedieron o que 
    terminaron hace menos de 30 minutos (margen de tolerancia).
    """
    # QUERY BASE DE ASIGNACIONES 
    query = (
        select(Clase)
        .join(ProfesorDictaClase, ProfesorDictaClase.id_clase == Clase.id)
        .filter(ProfesorDictaClase.id_profesor == profesor_id)
        .order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    )
    clases_objetos = db.session.scalars(query).all()
    
    # 🕒 Momento exacto de "ahora" respetando la zona horaria del sistema
    ahora = datetime.now(tz_arg).replace(tzinfo=None)
    
    clases_limpias = []
    
    for c in clases_objetos:
        # Combinamos la fecha de la clase y la hora de inicio en un datetime nativo
        inicio_datetime = datetime.combine(c.fecha_clase, c.horario)
        
        # Calculamos el límite de visibilidad: inicio + duración + 30 minutos de aire
        limite_visibilidad = inicio_datetime + timedelta(minutes=c.duracion + 30)
        
        # 🔥 FILTRO: Si el momento actual ya superó el límite de visibilidad, la ignoramos
        if ahora > limite_visibilidad:
            continue
            
        clases_limpias.append({
            "id": c.id,
            "nombre": c.nombre,
            "especialidad": c.especialidad,
            "duracion": c.duracion,
            "tipo": c.tipo,
            "fecha": c.fecha_clase,   
            "horario": c.horario,     
            "suspendida": c.suspendida,
            "sala_numero": c.sala.numero_puerta if c.sala else "N/A"
        })
        
    return clases_limpias

def resolver_postulacion_clase(postulacion_id: int, accion: str) -> bool:
    """
    Modifica el estado de una postulación.
    Si pertenece a una clase fija (bloque), aplica la acción (aceptar o rechazar) 
    en cascada a todas las instancias de dicho bloque para ese profesor.
    """
    postulacion = db.session.get(PostulacionClase, postulacion_id)
    if not postulacion or postulacion.estado != "PENDIENTE":
        return False  # No existe o ya fue resuelta

    # 1. 🔍 DETECTAR EL ALCANCE (¿Es clase fija/bloque o individual?)
    registro_bloque = db.session.scalar(
        select(ClaseBloque).filter(ClaseBloque.id_clase == postulacion.clase_id)
    )
    
    if registro_bloque:
        # 🔥 ES CLASE FIJA: Buscamos todas las clases asociadas al mismo bloque
        registros_del_bloque = db.session.scalars(
            select(ClaseBloque).filter(ClaseBloque.id_bloque == registro_bloque.id_bloque)
        ).all()
        clases_afectadas = [rb.id_clase for rb in registros_del_bloque]
    else:
        # 🟢 ES CLASE INDIVIDUAL: Solo afectará a la clase actual
        clases_afectadas = [postulacion.clase_id]

    # 2. 🔀 EJECUTAR FLUJO SEGÚN LA ACCIÓN
    if accion == "aceptar":
        # ✅ MARCAR POSTULACIONES COMO ACEPTADAS (Para este profesor en todo el bloque)
        postulaciones_ganadoras = db.session.scalars(
            select(PostulacionClase)
            .filter(
                PostulacionClase.profesor_id == postulacion.profesor_id,
                PostulacionClase.clase_id.in_(clases_afectadas),
                PostulacionClase.estado == "PENDIENTE"
            )
        ).all()
        
        for p_ganadora in postulaciones_ganadoras:
            p_ganadora.estado = "ACEPTADA"

        # IMPACTO EN LA TABLA DICTA (Asignación física de las clases)
        for clase_id in clases_afectadas:
            existe_dicta = db.session.scalar(
                select(ProfesorDictaClase).filter(
                    ProfesorDictaClase.id_profesor == postulacion.profesor_id, 
                    ProfesorDictaClase.id_clase == clase_id
                )
            )
            if not existe_dicta:
                db.session.add(ProfesorDictaClase(id_profesor=postulacion.profesor_id, id_clase=clase_id))
        
        # ❌ RECHAZAR EN CASCADA A LOS COMPETIDORES
        otras_postulaciones = db.session.scalars(
            select(PostulacionClase)
            .filter(
                PostulacionClase.clase_id.in_(clases_afectadas),
                PostulacionClase.profesor_id != postulacion.profesor_id,
                PostulacionClase.estado == "PENDIENTE"
            )
        ).all()
        
        for otra in otras_postulaciones:
            otra.estado = "RECHAZADA"
            
    elif accion == "rechazar":
        # ❌ RECHAZAR EN CASCADA AL MISMO PROFESOR EN TODO EL BLOQUE
        postulaciones_a_rechazar = db.session.scalars(
            select(PostulacionClase)
            .filter(
                PostulacionClase.profesor_id == postulacion.profesor_id,
                PostulacionClase.clase_id.in_(clases_afectadas),
                PostulacionClase.estado == "PENDIENTE"
            )
        ).all()

        for p_a_rechazar in postulaciones_a_rechazar:
            p_a_rechazar.estado = "RECHAZADA"
            
    else:
        return False

    # 3. 💾 TRANSACTAR CAMBIOS
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error transaccional al resolver postulación con bloque: {e}")
        return False

def conseguir_clase_actual (id_profesor):
    """Retorna la clase actual del profesor o None. profesor/index.html maneja None de manera adaptativa"""

    Profesor = aliased(Usuario)
    
    query = (
        db.session.query(Clase, func.count(
            Reserva.id
        ).label("reservas_totales"), func.coalesce(
            func.sum(case(
                (Reserva.asiste == AsistenciaReserva.PRESENTE, 1),
                else_=0
            )), 0
        ).label("asistencias_actuales"))

        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        # Las reglas de negocio no permiten que se de una clase sin alumnos, pero, dado el caso, outerjoin prepara el escenario
        .outerjoin(Reserva, Reserva.id_clase == Clase.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(*filtro_clase_actual())

        .group_by(Clase.id)
    )

    return db.session.execute(query).one_or_none()

def profesor_está_en_clase (id_profesor):
    """Retorna un valor booleano que representa si el profesor está en clase"""

    Profesor = aliased(Usuario)

    query = (
        db.session.query(Clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(*filtro_clase_actual())
    )

    return db.session.query(
        query.exists()
    ).scalar()

def clase_tiene_lugar(clase):

    cantidad_lugares_ocupados = (
        db.session.query(func.count(Reserva.id))
        .filter(Reserva.id_clase == clase.id)
        .filter(Reserva.asiste != AsistenciaReserva.CANCELADA)
    )

    ocupados = (db.session.scalar(cantidad_lugares_ocupados) or 0)

    return ocupados < clase.capacidad_maxima

def comprobar_alta_demanda (clase):
    """Devuelve true si hay que informar alta demanda, False si no hay que hacerlo o si ya se comprobó previamente"""
    
    if (not clase.aviso_alta_demanda) and (devolver_cantidad_esperando_en_cola (clase) == 10):
        clase.aviso_alta_demanda = True
        db.session.commit()
        return True
    return False
