import calendar
from datetime import date, datetime, time, timedelta
from sqlalchemy import or_, select, func, case, and_
from sqlalchemy.orm import aliased


from src.core.database import db
from src.core.clases.clases import Clase, ProfesorDictaClase, ClaseBloque, PostulacionClase
from src.core.reservas.reservas import Reserva, AsistenciaReserva, Cancelacion, EstadoCancelacion
from src.core.notificaciones import TipoNotificacion, enviar_notificaciones
from src.core.pagos import Beneficio, TipoBeneficio
from src.core.mail import enviar_correo

# <VER CLASES ADMIN>
def listar_clases():
    """
    Retorna las clases de rehabilitación que aún no han finalizado,
    calculando su término exacto en base a su duración.
    """
    ahora = datetime.now()
    hoy = ahora.date()

    query = (
        select(Clase)
        .where(Clase.fecha_clase >= hoy,
               Clase.aprobada == True)
        .order_by(
            Clase.fecha_clase.asc(), 
            Clase.horario.asc()
        )
    )
    clases_candidatas = db.session.scalars(query).all()

    clases_vigentes = []

    for clase in clases_candidatas:
        if clase.fecha_clase > hoy:
            clases_vigentes.append(clase)
        else:
            try:
                hora_inicio_str = clase.horario if isinstance(clase.horario, str) else clase.horario.strftime('%H:%M')
                dt_inicio = datetime.strptime(f"{hoy} {hora_inicio_str}", "%Y-%m-%d %H:%M")
                
                dt_fin = dt_inicio + timedelta(minutes=int(clase.duracion))
                
                if ahora <= dt_fin:
                    clases_vigentes.append(clase)
            except Exception as e:
                print(f"Error procesando horario de clase {clase.id}: {e}")
                clases_vigentes.append(clase)

    return clases_vigentes
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
    from src.core.usuarios.usuarios import Usuario, Profesor, Especialidad
    
    """
    Retorna los postulantes de una clase y la información del profesor asignado si existiese.
    Adaptado a la herencia polimórfica y Enums del nuevo esquema.
    """
    # Se crea un alias para el modelo Profesor para evitar advertencias de SAWarning
    # con uniones de tablas superpuestas en herencia de tabla unida.
    profesor_alias = aliased(Profesor)

    # 1. 🔍 VERIFICAR SI ALGUIEN YA DICTA ESTA CLASE ACTUALMENTE
    query_asignado = (
        select(
            Usuario.nombre,
            Usuario.apellido,
            Especialidad.nombre.label("especialidad_enum")
        )
        .join(ProfesorDictaClase, ProfesorDictaClase.id_profesor == Usuario.id)
        .join(profesor_alias, profesor_alias.id == Usuario.id)  # Uso de alias
        # Si el profesor no tiene especialidad, trae nombre/apellido y la especialidad vendrá como None
        .join(Especialidad, profesor_alias.id_especialidad == Especialidad.id, isouter=True)
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
        .join(profesor_alias, profesor_alias.id == Usuario.id)  # Uso de alias
        .join(Especialidad, profesor_alias.id_especialidad == Especialidad.id, isouter=True)
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
def obtener_horarios_disponibles(fecha_evaluar, duracion_minutos=45, sala_id_evaluar=0, tipo_clase="Individual", profesor_id=None):
    HORA_INICIO_LABORAL = 8
    HORA_FIN_LABORAL = 20
    INTERVALO_SLOTS = 30

    try:
        sala_id_evaluar = int(sala_id_evaluar)
    except (TypeError, ValueError):
        return []

    rangos_ocupados = []

    #  CONSTRUCCIÓN DE LA CONDICIÓN DE FILTRADO BASE
    # El horario está ocupado si la clase ya está aprobada por el admin...
    condicion_ocupacion = (Clase.aprobada == True)
    
    # ...O si la clase fue propuesta por ESTE mismo profesor y sigue pendiente.
    if profesor_id:
        from src.core.clases.clases import ProfesorDictaClase # Tu tabla intermedia
        
        # Subquery para traer los IDs de las clases que este profesor ya tiene asociadas
        subquery_mis_clases = select(ProfesorDictaClase.id_clase).where(
            ProfesorDictaClase.id_profesor == profesor_id
        )
        
        condicion_ocupacion = or_(
            Clase.aprobada == True,
            (Clase.id.in_(subquery_mis_clases)) & (Clase.aprobada == False)
        )

    if tipo_clase == "Fija":
        # --- LÓGICA PARA CLASES FIJAS ---
        anio = fecha_evaluar.year
        mes = fecha_evaluar.month
        dia_semana_python = fecha_evaluar.weekday()
        
        _, total_dias_mes = calendar.monthrange(anio, mes)
        otras_fechas_del_mes = []
        
        for dia in range(1, total_dias_mes + 1):
            fecha_posible = datetime(anio, mes, dia).date()
            if fecha_posible.weekday() == dia_semana_python and fecha_posible != fecha_evaluar:
                otras_fechas_del_mes.append(fecha_posible)
        
        # Aplicamos la condicion_ocupacion combinada con tus filtros de fechas
        query = select(Clase).filter(
            Clase.sala_id == sala_id_evaluar,
            Clase.suspendida == False,
            condicion_ocupacion, #  Inyección del blindaje por rol
            or_(
                (Clase.fecha_clase == fecha_evaluar),
                (Clase.fecha_clase.in_(otras_fechas_del_mes)) & (Clase.tipo == "Individual")
            )
        )
        clases_conflictivas = db.session.scalars(query).all()

        for c in clases_conflictivas:
            inicio_dt = datetime.combine(fecha_evaluar, c.horario)
            fin_dt = inicio_dt + timedelta(minutes=c.duracion)
            rangos_ocupados.append((inicio_dt, fin_dt))

    else:
        # --- LÓGICA PARA CLASE INDIVIDUAL (Y PROPUESTAS DE PROFESOR) ---
        
        # 1. Traemos todas las clases YA APROBADAS en la sala seleccionada para ese día
        query_sala = select(Clase).filter(
            Clase.fecha_clase == fecha_evaluar,
            Clase.sala_id == sala_id_evaluar,
            Clase.suspendida == False,
            Clase.aprobada == True # Solo las clases confirmadas bloquean la sala
        )
        clases_en_sala = db.session.scalars(query_sala).all()
        
        clases_a_considerar = list(clases_en_sala)
        ids_vistos = {c.id for c in clases_en_sala}

        # 2. Si es un profesor, agregamos todos sus compromisos de ese día (en cualquier sala)
        if profesor_id:
            # Clases que el profesor TIENE (dicta o propuso y están pendientes)
            clases_propias = db.session.scalars(
                select(Clase)
                .join(ProfesorDictaClase, ProfesorDictaClase.id_clase == Clase.id)
                .filter(
                    ProfesorDictaClase.id_profesor == profesor_id,
                    Clase.fecha_clase == fecha_evaluar,
                    Clase.suspendida == False
                )
            ).all()

            # Postulaciones PENDIENTES o ACEPTADAS que tenga a otras clases
            postulaciones = db.session.scalars(
                select(Clase)
                .join(PostulacionClase, PostulacionClase.clase_id == Clase.id)
                .filter(
                    PostulacionClase.profesor_id == profesor_id,
                    Clase.fecha_clase == fecha_evaluar,
                    PostulacionClase.estado.in_(['PENDIENTE', 'ACEPTADA'])
                )
            ).all()
            
            # Unificamos las listas evitando duplicados
            for clase_prof in clases_propias + postulaciones:
                if clase_prof.id not in ids_vistos:
                    clases_a_considerar.append(clase_prof)
                    ids_vistos.add(clase_prof.id)

        for c in clases_a_considerar:
            inicio_dt = datetime.combine(fecha_evaluar, c.horario)
            fin_dt = inicio_dt + timedelta(minutes=c.duracion)
            rangos_ocupados.append((inicio_dt, fin_dt))

    # --- GENERADOR DE SLOTS (Se mantiene igual de óptimo) ---
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
    from src.core.usuarios.usuarios import Especialidad
    """
    Retorna la lista real de especialidades ordenadas alfabéticamente
    directo desde la base de datos.
    """
    # Ordenamos usando el valor en texto del Enum
    query = select(Especialidad).order_by(Especialidad.nombre.asc())
    especialidades = db.session.scalars(query).all()
    return especialidades

def crear_clases_agenda(id_profesor=None, **datos_clase):
    """
    Se encarga de persistir las clases en la base de datos con manejo estricto de excepciones.
    Permite opcionalmente vincular un profesor a cada instancia creada en la agenda.
    """
    try:
        from src.core.clases import validar_disponibilidad_extendida
        from src.web.helpers.feriados import obtener_dias_no_laborables
        fecha_inicial = datos_clase.get('fecha_clase')
        tipo = datos_clase.get('tipo') or datos_clase.get('tipo_clase')
        
        fechas_a_procesar = []
        hoy = date.today()

        if tipo == "Fija":
            anio = fecha_inicial.year
            mes = fecha_inicial.month
            dia_semana_objetivo = fecha_inicial.weekday()

            # Obtenemos los feriados para evitar crear clases en esos días
            feriados_del_anio = obtener_dias_no_laborables(anio)

            cal = calendar.monthcalendar(anio, mes)
            for semana in cal:
                dia = semana[dia_semana_objetivo]
                if dia != 0:
                    fecha_calculada = date(anio, mes, dia)
                    # 🔥 NUEVA VALIDACIÓN: Solo procesar si es futuro Y NO es feriado
                    if fecha_calculada >= hoy and fecha_calculada.strftime('%Y-%m-%d') not in feriados_del_anio:
                        fechas_a_procesar.append(fecha_calculada)
        else:
            fechas_a_procesar.append(fecha_inicial)

        if not fechas_a_procesar:
            print(f"⚠️ Alerta Seeder/Agenda: No se generaron fechas para {fecha_inicial} [Tipo: {tipo}]")
            return False

        id_bloque_actual = None
        if tipo == "Fija":
            max_bloque = db.session.scalar(select(func.max(ClaseBloque.id_bloque)))
            id_bloque_actual = (max_bloque + 1) if max_bloque is not None else 1

        # Guardamos cada registro en la BD
        for f in fechas_a_procesar:
            # 🔥 NUEVA VALIDACIÓN: Chequeo de disponibilidad de sala para esta fecha específica
            disponible, _ = validar_disponibilidad_extendida(
                db.session,
                Clase,
                datos_clase.get('sala_id'),
                f, # La fecha que estamos por procesar
                datos_clase.get('horario'),
                datos_clase.get('duracion'),
                "Individual" # Validamos como si fuera una clase individual para chequear solo este día
            )
            if not disponible:
                print(f"⚠️ Omitiendo creación de clase en fecha {f.strftime('%Y-%m-%d')} por conflicto de horario/sala.")
                continue # Saltamos a la siguiente fecha sin crear esta instancia

            nueva_clase = Clase(
                nombre=datos_clase.get('nombre'),
                especialidad=datos_clase.get('especialidad'),
                duracion=datos_clase.get('duracion'),
                descripcion=datos_clase.get('descripcion'),
                fecha_clase=f,
                horario=datos_clase.get('horario'),
                tipo=tipo,
                sala_id=datos_clase.get('sala_id'),
                suspendida=False,
                aprobada=True
            )
            db.session.add(nueva_clase)

            # BLINDAJE ATÓMICO: Cancelamos cualquier propuesta que compita con este slot
            _limpiar_propuestas_por_colision(nueva_clase)
            
            # NUEVA LÓGICA: Si se provee un profesor, creamos la relación intermedia
            if id_profesor is not None:
                # Usamos el objeto completa 'clase=nueva_clase' para que SQLAlchemy
                # resuelva los IDs autoincrementales automáticamente en el flush/commit.
                nueva_relacion = ProfesorDictaClase(
                    id_profesor=id_profesor,
                    id_clase=nueva_clase.id
                )
                db.session.add(nueva_relacion)
            
            if tipo == "Fija":
                db.session.flush() # Forzamos obtención de ID de clase para el bloque
                
                asociacion_bloque = ClaseBloque(
                    id_bloque=id_bloque_actual,
                    id_clase=nueva_clase.id
                )
                db.session.add(asociacion_bloque)

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error crítico en el Core al persistir la agenda: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
# <CREAR CLASE/>

# <POSTULACION DE PROFESORES>
def obtener_clases_disponibles_para_profesor(profesor_id):
    from src.core.usuarios.usuarios import Profesor, Especialidad
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
                PostulacionClase.profesor_id == profesor_id,
                PostulacionClase.estado.in_(["PENDIENTE", "ACEPTADA", "RECHAZADA"])
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
    from src.core.clases.clases import tz_arg
    """
    Trae las clases asignadas a un profesor que aún no sucedieron o que 
    terminaron hace menos de 30 minutos (margen de tolerancia).
    """
    # QUERY BASE DE ASIGNACIONES 
    query = (
    select(Clase)
    .join(ProfesorDictaClase, ProfesorDictaClase.id_clase == Clase.id)
    .where(
        ProfesorDictaClase.id_profesor == profesor_id,
        Clase.aprobada == True  # 🔓 Solo muestra las clases confirmadas por el Admin
    )
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
    from src.core.usuarios import obtener_usuario_por_id_core
    from src.core.clases.clases import PostulacionClase # Asegurar imports correctos
    
    postulacion = db.session.get(PostulacionClase, postulacion_id)
    if not postulacion or postulacion.estado != "PENDIENTE":
        return False  # No existe o ya fue resuelta

    clase = db.session.scalar(
        select(Clase).filter(Clase.id == postulacion.clase_id)
    )
    
    # 1. DETECTAR EL ALCANCE (¿Es clase fija/bloque o individual?)
    registro_bloque = db.session.scalar(
        select(ClaseBloque).filter(ClaseBloque.id_clase == postulacion.clase_id)
    )
    
    if registro_bloque:
        # ES CLASE FIJA: Buscamos todas las clases asociadas al mismo bloque
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

        # IMPACTO EN LA TABLA DICTA (Asignación física de las clases no suspendidas)
        for clase_id in clases_afectadas:
            # COMPROBACIÓN: Si la instancia específica está suspendida, no creamos asignación
            instancia_clase = db.session.get(Clase, clase_id)
            if instancia_clase and instancia_clase.suspendida:
                continue

            existe_dicta = db.session.scalar(
                select(ProfesorDictaClase).filter(
                    ProfesorDictaClase.id_profesor == postulacion.profesor_id, 
                    ProfesorDictaClase.id_clase == clase_id
                )
            )
            if not existe_dicta:
                db.session.add(ProfesorDictaClase(id_profesor=postulacion.profesor_id, id_clase=clase_id))
        
        enviar_notificaciones(obtener_usuario_por_id_core(postulacion.profesor_id), "¡Se ha aprobado la postulación de la clase!", f"Se ha aprobado su participación en la clase {clase.nombre}. Para más información vaya a la sección 'Mis clases' en el navegador de profesores.", TipoNotificacion.ESTADO_POSTULACION_CLASE)
        
        # RECHAZAR EN CASCADA A LOS COMPETIDORES
        otras_postulaciones = db.session.scalars(
            select(PostulacionClase)
            .filter(
                PostulacionClase.clase_id.in_(clases_afectadas),
                PostulacionClase.profesor_id != postulacion.profesor_id,
                PostulacionClase.estado == "PENDIENTE"
            )
        ).all()
        
        profesores_a_notificar = set()
        for otra in otras_postulaciones:
            otra.estado = "RECHAZADA"
            profesores_a_notificar.add(otra.profesor_id)
        
        # Notificación corregida a cada usuario competente
        for prof_id in profesores_a_notificar:
            usuario_competidor = obtener_usuario_por_id_core(prof_id)
            if usuario_competidor:
                enviar_notificaciones(usuario_competidor, "Se ha rechazado su postulación a clase", f"Se ha rechazado su participación en la clase {clase.nombre}.", TipoNotificacion.ESTADO_POSTULACION_CLASE)
            
    elif accion == "rechazar":
        # RECHAZAR EN CASCADA AL MISMO PROFESOR EN TODO EL BLOQUE
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
        
        enviar_notificaciones(obtener_usuario_por_id_core(postulacion.profesor_id), "Se ha rechazado su postulación a clase", f"Se ha rechazado su participación en la clase {clase.nombre}.", TipoNotificacion.ESTADO_POSTULACION_CLASE)
            
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
    from src.core.functions import filtro_clase_actual
    from src.core.usuarios.usuarios import Usuario, RolUsuario
    """Retorna la clase actual del profesor o None. profesor/index.html maneja None de manera adaptativa"""

    Profesor = aliased(Usuario)
    
    query = (
        db.session.query(Clase, func.coalesce(
                func.sum(case(
                    (Reserva.asiste != AsistenciaReserva.CANCELADA, 1),
                    else_=0
                )), 0
            ).label("reservas_totales"),
            func.coalesce
                (func.sum(case(
                    (Reserva.asiste == AsistenciaReserva.PRESENTE, 1),
                    else_=0
                )), 0
            ).label("asistencias_actuales")
        )

        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .join(Profesor, ProfesorDictaClase.id_profesor == Profesor.id)
        .join(Reserva, Reserva.id_clase == Clase.id)

        .filter(Profesor.id == id_profesor)
        .filter(Profesor.rol == RolUsuario.PROFESOR)
        .filter(*filtro_clase_actual())

        .group_by(Clase.id)
    )
    print (db.session.execute(query).one_or_none())

    return db.session.execute(query).one_or_none()

def profesor_está_en_clase (id_profesor):
    from src.core.functions import filtro_clase_actual
    from src.core.usuarios.usuarios import Usuario, RolUsuario
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

    if not clase.sala:
        return False
    return ocupados < clase.sala.capacidad

def comprobar_alta_demanda (clase):
    from src.core.reservas import devolver_cantidad_esperando_en_cola
    """Devuelve true si hay que informar alta demanda, False si no hay que hacerlo o si ya se comprobó previamente"""
    
    if (not clase.aviso_alta_demanda) and (devolver_cantidad_esperando_en_cola (clase) == 10):
        clase.aviso_alta_demanda = True
        db.session.commit()
        return True
    return False

def tiene_qr (clase_actual):
    query = (db.session.query(Clase)
        .filter (Clase.id == clase_actual.id)
        .filter (Clase.token_qr != None)
    )
    return db.session.query(
        query.exists()
    ).scalar()

def procesar_suspension_clase(clase_id, tz_arg=None):
    """
    Orquestador del Core para alternar el estado de suspensión de una clase.
    Aplica compensaciones a alumnos y anula flujos de profesores en caso de suspensión.
    """
    clase = db.session.get(Clase, clase_id)
    if not clase:
        return {"status": "danger", "message": "La clase solicitada no existe."}
        
    # --- Validación de tiempo de finalización ---
    inicio_clase = datetime.combine(clase.fecha_clase, clase.horario)
    fin_clase = inicio_clase + timedelta(minutes=clase.duracion)
    ahora = datetime.now(tz_arg).replace(tzinfo=None) if tz_arg else datetime.now()
    
    if ahora >= fin_clase:
        return {
            "status": "warning", 
            "message": f"No se puede modificar la clase '{clase.nombre}' porque ya ha finalizado."
        }
    # ------------------------------------------------------

    try:
        clase.suspendida = True
        
        # 1. Modularización Alumnos: Compensación de Créditos y Cancelaciones
        _procesar_compensacion_alumnos(clase, ahora)
        
        # 2. Modularización Profesores: Anulación de Postulaciones y Asignaciones
        _procesar_baja_profesores_y_postulaciones(clase.id, clase.nombre, clase.fecha_clase)

        # Confirmar toda la transacción unificada
        db.session.commit()
        
        return {
            "status": "success", 
            "message": f"La clase '{clase.nombre}' fue suspendida con éxito. Se liberaron profesores y se compensó a los alumnos."
        }

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error crítico en el servicio de suspensión: {e}")
        return {
            "status": "danger", 
            "message": "Hubo un error interno al procesar la suspensión. No se alteraron los datos."
        }


# --- FUNCIONES AUXILIARES EXTRAÍDAS (MANTENIMIENTO LIMPIO) ---

def _procesar_compensacion_alumnos(clase, ahora):
    """Procesa el impacto de la suspensión sobre las reservas activas de los clientes."""
    query_reservas = select(Reserva).where(
        Reserva.id_clase == clase.id,
        ~Reserva.cancelaciones.any()
    )
    reservas_activas = db.session.scalars(query_reservas).all()
    
    for reserva in reservas_activas:
        # Actualizar estado de la reserva
        reserva.asiste = AsistenciaReserva.CANCELADA

        # Crear la cancelación institucional
        nueva_cancelacion = Cancelacion(
            id_reserva=reserva.id,
            descripcion="Clase suspendida por motivos institucionales (Centro de Rehabilitación).",
            estado=EstadoCancelacion.CORRESPONDE_ACREDITAR_SIN_LIMITES
        )
        db.session.add(nueva_cancelacion)
        
        # Generar el beneficio (Crédito)
        nuevo_credito = Beneficio(
            id_pago=None,
            id_cliente=reserva.id_cliente,
            tipo=TipoBeneficio.CREDITO,
            descripcion=f"Compensación automática por suspensión de clase: {clase.nombre}",
            # fecha_vencimiento=ahora + timedelta(days=30),
            usado=False
        )
        db.session.add(nuevo_credito)
        
        # Notificar al cliente
        asunto = f"AVISO IMPORTANTE: Clase Suspendida - {clase.nombre}"
        cuerpo = (
            f"Estimado paciente,\n\n"
            f"Le informamos que la clase de '{clase.nombre}' programada para el día "
            f"{clase.fecha_clase.strftime('%d/%m/%Y')} a las {clase.horario.strftime('%H:%M')} hs ha sido SUSPENDIDA.\n\n"
            f"Se ha acreditado automáticamente un crédito en su cuenta para que pueda reprogramar su turno.\n\n"
            f"Disculpe las molestias.\n"
            f"Atentamente, Administración de RehabilitAR."
        )
        enviar_notificaciones(reserva.cliente, asunto, cuerpo, TipoNotificacion.CLASE_SUSPENDIDA)


def _procesar_baja_profesores_y_postulaciones(clase_id: int, clase_nombre: str, clase_fecha):
    """Procesa el impacto de la suspensión sobre el cuerpo docente y postulantes."""
    from src.core.usuarios import obtener_usuario_por_id_core

    # 1. Cancelar en cascada postulaciones activas a estado "SUSPENDIDA"
    postulaciones_afectadas = db.session.scalars(
        select(PostulacionClase).filter(
            PostulacionClase.clase_id == clase_id,
            PostulacionClase.estado.in_(["PENDIENTE", "ACEPTADA"])
        )
    ).all()

    profesores_a_notificar = set()
    for postu in postulaciones_afectadas:
        postu.estado = "SUSPENDIDA"
        profesores_a_notificar.add(postu.profesor_id)

    # 2. DELETE físico del dueño en ProfesorDictaClase
    asignaciones_actuales = db.session.scalars(
        select(ProfesorDictaClase).filter(ProfesorDictaClase.id_clase == clase_id)
    ).all()
    
    for asignacion in asignaciones_actuales:
        db.session.delete(asignacion)

    # 3. Notificar de forma atómica a cada profesor involucrado
    for prof_id in profesores_a_notificar:
        profesor = obtener_usuario_por_id_core(prof_id)
        if profesor:
            enviar_notificaciones(
                profesor,
                "Clase Suspendida",
                f"Te informamos que la clase '{clase_nombre}' programada para el día {clase_fecha.strftime('%d/%m/%Y')} ha sido suspendida por la institución. Las postulaciones asociadas quedan sin efecto.",
                TipoNotificacion.ESTADO_POSTULACION_CLASE
            )
def profesor_tiene_conflicto_horario(clase_id, id_profesor):
    """Dada una clase y el id_profesor, comprueba si existe otra clase que se de a la vez que la primera. En caso de no existir clase devuelve false, caso contrario devuelve un texto preparado para meter en flash()"""
    from src.core.clases import PostulacionClase

    clase = obtener_clase_por_id(clase_id)

    inicio_nuevo = datetime.combine(clase.fecha_clase, clase.horario)
    fin_nuevo = inicio_nuevo + timedelta(minutes = clase.duracion)

    # Primero agarramos las clases del profe
    clases_profesor = (db.session.query(Clase)
        .join(ProfesorDictaClase, ProfesorDictaClase.id_clase == Clase.id)
        .filter(ProfesorDictaClase.id_profesor == id_profesor)
        .filter(Clase.fecha_clase == clase.fecha_clase)
        .filter(Clase.suspendida != False)
        .all()
    )

    # Sumamos sus postulaciones
    postulaciones_profesor = (db.session.query(Clase)
        .join (PostulacionClase, Clase.id == PostulacionClase.clase_id)
        .filter(PostulacionClase.profesor_id == id_profesor)
        .filter(Clase.fecha_clase == clase.fecha_clase)
        .filter(PostulacionClase.estado != "RECHAZADA")
        .all()
    )

    clases_profesor.extend(postulaciones_profesor)

    for otra in clases_profesor:
        if otra.id == clase.id:
            continue

        inicio_otra = datetime.combine(otra.fecha_clase, otra.horario)
        fin_otra = inicio_otra + timedelta(minutes = otra.duracion)

        if (inicio_nuevo < fin_otra and fin_nuevo > inicio_otra):
            return otra.nombre

    return False

def _limpiar_propuestas_por_colision(nueva_clase_admin):
    """
    Busca propuestas de profesores (aprobada=False, suspendida=False) que colisionen 
    en la misma fecha y sala que la nueva clase oficial del Admin, pasándolas a suspendida=True.
    """
    inicio_admin = datetime.combine(nueva_clase_admin.fecha_clase, nueva_clase_admin.horario)
    fin_admin = inicio_admin + timedelta(minutes=nueva_clase_admin.duracion)
    
    # Traemos solo las propuestas pendientes de esa sala y fecha
    query_propuestas = select(Clase).filter(
        Clase.fecha_clase == nueva_clase_admin.fecha_clase,
        Clase.sala_id == nueva_clase_admin.sala_id,
        Clase.aprobada == False,
        Clase.suspendida == False
    )
    propuestas_candidatas = db.session.scalars(query_propuestas).all()
    
    for propuesta in propuestas_candidatas:
        inicio_propu = datetime.combine(propuesta.fecha_clase, propuesta.horario)
        fin_propu = inicio_propu + timedelta(minutes=propuesta.duracion)
        
        # Superposición: InicioA < FinB and FinA > InicioB
        if inicio_admin < fin_propu and fin_admin > inicio_propu:
            propuesta.suspendida = True # Muta a Rechazada por Colisión

def profesor_tiene_conflicto_horario_propuesta(id_profesor, fecha_clase, horario, duracion):
    """
    Dada la información de una propuesta de clase y el id_profesor, comprueba si existe
    otra clase o postulación que se solape en el tiempo.
    Devuelve el nombre de la clase conflictiva si existe, caso contrario False.
    """
    from src.core.clases.clases import PostulacionClase, ProfesorDictaClase

    inicio_nuevo = datetime.combine(fecha_clase, horario)
    fin_nuevo = inicio_nuevo + timedelta(minutes=duracion)

    # Clases que el profesor TIENE (dicta o propuso y están pendientes)
    clases_del_profesor = (db.session.query(Clase)
        .join(ProfesorDictaClase, ProfesorDictaClase.id_clase == Clase.id)
        .filter(ProfesorDictaClase.id_profesor == id_profesor)
        .filter(Clase.fecha_clase == fecha_clase)
        .filter(Clase.suspendida == False)
        .all()
    )

    # Postulaciones PENDIENTES o ACEPTADAS que tenga el profesor a otras clases
    postulaciones_del_profesor = (db.session.query(Clase)
        .join(PostulacionClase, PostulacionClase.clase_id == Clase.id)
        .filter(PostulacionClase.profesor_id == id_profesor)
        .filter(Clase.fecha_clase == fecha_clase)
        .filter(PostulacionClase.estado.in_(['PENDIENTE', 'ACEPTADA']))
        .all()
    )

    # Combinamos ambas listas y eliminamos duplicados si los hubiera
    ids_vistos = set()
    todas_las_clases_relevantes = []
    for clase in clases_del_profesor + postulaciones_del_profesor:
        if clase.id not in ids_vistos:
            todas_las_clases_relevantes.append(clase)
            ids_vistos.add(clase.id)

    for clase_existente in todas_las_clases_relevantes:
        inicio_existente = datetime.combine(clase_existente.fecha_clase, clase_existente.horario)
        fin_existente = inicio_existente + timedelta(minutes=clase_existente.duracion)

        # Comprobación de solapamiento: (InicioA < FinB) y (FinA > InicioB)
        if (inicio_nuevo < fin_existente and fin_nuevo > inicio_existente):
            return clase_existente.nombre # Devuelve el nombre para el mensaje de error

    return False

def proponer_clase_profesor(profesor_id: int, **datos_propuesta) -> bool:
    """
    Permite a un profesor registrar una propuesta de clase individual.
    Nace con aprobada=False y se pre-asigna en ProfesorDictaClase.
    """
    from src.core.clases.clases import ProfesorDictaClase

    try:
        fecha_inicial = datos_propuesta.get('fecha_clase')
        
        # Por regla de negocio elemental, las propuestas de profesores suelen ser individuales 
        # para que el administrador las evalúe caso por caso.
        nueva_propuesta = Clase(
            nombre=datos_propuesta.get('nombre'),
            especialidad=datos_propuesta.get('especialidad'),
            duracion=datos_propuesta.get('duracion'),
            descripcion=datos_propuesta.get('descripcion'),
            fecha_clase=fecha_inicial,
            horario=datos_propuesta.get('horario'),
            tipo="Individual",
            sala_id=datos_propuesta.get('sala_id'),
            suspendida=False,
            aprobada=False # 🟡 Estado: PROPUESTA / PENDIENTE
        )
        db.session.add(nueva_propuesta)
        db.session.flush() # Forzamos obtención del ID para la pre-asignación
        
        # Pre-vinculamos al profesor que la ideó para mantener la consistencia
        pre_asignacion = ProfesorDictaClase(
            id_profesor=profesor_id,
            id_clase=nueva_propuesta.id
        )
        db.session.add(pre_asignacion)
        
        db.session.commit()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al persistir la propuesta del profesor: {e}")
        return False
    
def validar_disponibilidad_extendida(db_session, Clase, sala_id, fecha_inicio, horario, duracion, tipo_clase):
    """
    Calcula las fechas correspondientes (un solo día o todo el mes si es Fija)
    y verifica si existen solapamientos horarios en la base de datos.
    Retorna (True, None) si está disponible, o (False, fecha_conflicto) si hay colisión.
    """
    # 1. Determinar el set de fechas a auditar
    fechas_a_validar = []
    if tipo_clase == "Individual":
        fechas_a_validar.append(fecha_inicio)
    else:
        fecha_corriente = fecha_inicio
        ultimo_dia_mes = calendar.monthrange(fecha_corriente.year, fecha_corriente.month)[1]
        fecha_limite = date(fecha_corriente.year, fecha_corriente.month, ultimo_dia_mes)
        
        while fecha_corriente <= fecha_limite:
            fechas_a_validar.append(fecha_corriente)
            fecha_corriente += timedelta(days=7)

    # 2. Rango horario de la nueva propuesta
    base_dt = datetime.combine(date.today(), horario)
    fin_propuesta_time = (base_dt + timedelta(minutes=duracion)).time()

    # 3. Comprobación en bucle
    for fecha in fechas_a_validar:
        clases_del_dia = db_session.scalars(
            select(Clase).where(
                Clase.sala_id == sala_id,
                Clase.fecha_clase == fecha,
                Clase.aprobada == True,
                Clase.suspendida == False
            )
        ).all()

        for clase in clases_del_dia:
            base_existente_dt = datetime.combine(date.today(), clase.horario)
            fin_existente_time = (base_existente_dt + timedelta(minutes=clase.duracion)).time()
            
            # Regla de solapamiento: (InicioA < FinB) AND (FinA > InicioB)
            if horario < fin_existente_time and fin_propuesta_time > clase.horario:
                return False, fecha

    return True, None
