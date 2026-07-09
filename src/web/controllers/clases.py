from datetime import date, datetime
from src.core.database import db
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from src.core.clases import crear_clases_agenda, listar_clases, listar_especialidades_activas, obtener_clase_por_id, obtener_horarios_disponibles, obtener_postulantes_clase, proponer_clase_profesor, resolver_postulacion_clase
from src.core.salas import listar_salas_habilitadas, obtener_sala
from src.web.helpers.feriados import obtener_dias_no_laborables
from src.core.clases.clases import Clase, PostulacionClase, ProfesorDictaClase
from src.core.auditoria import registrar_log, TipoAccion
from src.core.clases import obtener_clases_dictadas_por_profesor, obtener_clases_disponibles_para_profesor, obtener_postulaciones_de_profesor
from src.web.helpers.decorator import requiere_rol
from src.core.notificaciones import TipoNotificacion, enviar_notificaciones
from sqlalchemy import select

bp = Blueprint("clases", __name__, url_prefix="/clases")

@bp.get("/admin")
@requiere_rol(['ADMINISTRADOR'])
def listar_clases_admin():
    """Ruta que muestra el listado de clases para el administrador."""
    clases_registradas = listar_clases()
    return render_template("clases/clases_creadas.html", clases=clases_registradas, current_path=request.path)

@bp.get("/admin/<int:clase_id>")
@requiere_rol(['ADMINISTRADOR'])
def ver_detalle_admin(clase_id):
    """Ruta que delega la búsqueda al core y renderiza el detalle de la clase."""
    
    # 1. Le pedimos al core que busque la clase
    clase = obtener_clase_por_id(clase_id)
    
    # 2. El controlador maneja el error de cara al cliente web (HTTP 404)
    if not clase:
        return abort(404, description="La clase de rehabilitación no existe.")
    
    # 3. Le pedimos al core los datos de postulaciones (recibe el dict con postulantes y asignado)
    datos_postu = obtener_postulantes_clase(clase_id)
    
    # 4. Renderizamos la vista enviando los datos limpios por separado para Jinja
    return render_template(
        "clases/clase_detalle.html", 
        clase=clase, 
        postulantes=datos_postu["postulantes"],  # La lista de los que se anotaron
        asignado=datos_postu["asignado"],        # El diccionario del profe que la dicta (o None)
        current_path=request.path
    )

#Muestra el formulario al usuario
@bp.route('/nueva', methods=['GET'])
@requiere_rol(['ADMINISTRADOR'])
def nueva_clase():
    """
    Se activa cuando el usuario hace clic en 'Nueva Clase'.
    Busca las especialidades en el Core y dibuja el formulario.
    """
    # Le pedimos al Core las especialidades y las salas habilitadas para el select del HTML
    especialidades = listar_especialidades_activas()
    salas = listar_salas_habilitadas()

    # Obtenemos los días no laborables para el año actual y el siguiente
    # Obtenemos los días no laborables para el año actual y el siguiente para el calendario
    año_actual = datetime.now().year
    dias_no_laborables = obtener_dias_no_laborables(año_actual) + obtener_dias_no_laborables(año_actual + 1)

    return render_template('clases/crear_clase.html',
                           templates_especialidades=especialidades, 
                           puertas_salas=salas,
                           dias_no_laborables=dias_no_laborables)

@bp.route('/api/horarios-disponibles', methods=['GET'])
def api_horarios_disponibles():
    fecha_str = request.args.get('fecha')
    duracion_str = request.args.get('duracion', '45')
    sala_id = request.args.get('sala_id')
    tipo_clase = request.args.get('tipo', 'Individual')

    if not fecha_str:
        return jsonify([]), 400

    try:
        fecha_evaluar = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        duracion = int(duracion_str)
        
        profesor_id_evaluar = None
        if session.get('rol') == 'PROFESOR':
            profesor_id_evaluar = session.get('usuario_id')

        # Le pedimos la info al Core pasando el parámetro real
        libres = obtener_horarios_disponibles(
            fecha_evaluar, 
            duracion, 
            int(sala_id), 
            tipo_clase, 
            profesor_id=profesor_id_evaluar
        )
        return jsonify(libres)
    except ValueError:
        return jsonify([]), 400
    

# EL PROCESADOR (Recibe los datos cuando el usuario aprieta "Guardar")

@bp.route('/crear', methods=['POST'])
@requiere_rol(['ADMINISTRADOR'])
def crear_clase_post():
    """
    Ataja el formulario por POST, adapta los nombres de los campos
    a las columnas reales del modelo 'Clase' y limpia los tipos de datos.
    """
    # 1. Extracción de datos desde el HTML
    nombre = request.form.get('nombre')
    especialidad_id_str = request.form.get('especialidad_id')
    tipo_clase = request.form.get('tipo_clase')
    fecha_str = request.form.get('fecha_clase')
    horario_str = request.form.get('horario')
    duracion_str = request.form.get('duracion')
    # capacidad_str = request.form.get('capacidad_maxima')
    descripcion = request.form.get('descripcion')
    sala_id_str = request.form.get('sala_id')

    # 2. Conversión de tipos y formatos de datos
    try:
        fecha_clase = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        horario = datetime.strptime(horario_str, '%H:%M').time()
        duracion = int(duracion_str)
        # capacidad_maxima = int(capacidad_str)
        sala_id = int(sala_id_str)

        # Bloqueo de fechas anteriores
        if fecha_clase <= datetime.now().date():
            flash('La fecha debe ser a partir de mañana.', 'danger')
            return redirect(url_for('clases.nueva_clase'))

        # .weekday() devuelve: 5 = Sábado, 6 = Domingo
        if fecha_clase.weekday() in [5, 6]: 
            flash('No se pueden programar clases los fines de semana.', 'danger')
            return redirect(url_for('clases.nueva_clase'))
        
        # 🔍 BUSQUEDA CON EXTRACCIÓN DE ENUM
        especialidades_mock = listar_especialidades_activas()
        especialidad_nombre = "General" 
        
        for esp in especialidades_mock:       
            if str(esp.id) == especialidad_id_str:
                # CAMBIO CLAVE: Si es un objeto Enum, extraemos su .value ("TREN SUPERIOR")
                # Si por alguna razón ya fuese un string, se guarda directamente.
                if hasattr(esp.nombre, 'value'):
                    especialidad_nombre = esp.nombre.value
                else:
                    especialidad_nombre = esp.nombre
                break
        
        sala_elegida = obtener_sala(sala_id)
        if not sala_elegida:
            flash('La sala seleccionada no es válida.', 'danger')
            return redirect(url_for('clases.nueva_clase'))

        #if capacidad_maxima > sala_elegida.capacidad:
        #    flash(f'Error: La capacidad máxima para esta clase supera el límite físico de la Sala {sala_elegida.numero_puerta} (Máximo: {sala_elegida.capacidad} personas).', 'danger')
        #    return redirect(url_for('clases.nueva_clase'))

    except (ValueError, TypeError) as e:
        flash('Error en el formato de los datos obligatorios.', 'danger')
        return redirect(url_for('clases.nueva_clase'))

    # Ahora 'especialidad' recibe un string puro ("TREN SUPERIOR"), compatible con el modelo Clase
    exito = crear_clases_agenda(
        nombre=nombre,
        especialidad=especialidad_nombre,
        tipo=tipo_clase,
        fecha_clase=fecha_clase,
        horario=horario,
        duracion=duracion,
        #capacidad_maxima=capacidad_maxima,
        descripcion=descripcion,
        sala_id=sala_id
    )

    registrar_log(TipoAccion.CREACION_CLASE, detalles={
        'nombre': nombre,
        'tipo': tipo_clase,
        'fecha': fecha_str,
        'sala_id': sala_id
    })

    if exito:
        if (tipo_clase == "Individual"):
            flash("Clase individual creada con éxito", "success")
        elif (tipo_clase == "Fija"):
            flash("Clase fija creada con éxito. Se han creado instancias de la clase hasta final del mes", "success")
        else:
            flash('Clase(s) programada(s) con éxito para el mes en curso.', 'success')
    else:
        flash('No se pudieron programar clases (las fechas calculadas ya pasaron).', 'warning')

    return redirect(url_for('clases.listar_clases_admin'))


@bp.post("/admin/postulacion/<int:postu_id>/<string:accion>")
@requiere_rol(['ADMINISTRADOR'])
def responder_postulacion(postu_id, accion):
    """
    Procesa la decisión del administrador (aceptar/rechazar) sobre una postulación.
    """
    # 1. Seguridad: Validar que la acción sea válida de entrada
    if accion not in ["aceptar", "rechazar"]:
        return abort(400, description="Acción inválida. Solo se permite aceptar o rechazar.")

    # 2. Conseguir la postulación para saber a qué clase redirigir después del cambio
    from src.core.clases.clases import PostulacionClase
    postulacion = db.session.get(PostulacionClase, postu_id)
    if not postulacion:
        return abort(404, description="La postulación especificada no existe.")
    
    clase_id = postulacion.clase_id  # Guardamos el ID antes de operar para la redirección

    # Delegar la transacción al Core
    exito = resolver_postulacion_clase(postu_id, accion)
    registrar_log(TipoAccion.RESOLUCION_POSTULACION, id_entidad_objetivo=postu_id, detalles={'accion': accion, 'clase_id': clase_id})

    # Mensajes Flash basados en el resultado de la operación
    if exito:
        if accion == "aceptar":
            flash("¡Postulación aceptada con éxito! El profesor fue asignado y se liberó la cartelera.", "success")
        else:
            flash("La postulación ha sido rechazada correctamente.", "info")
    else:
        flash("Hubo un error al procesar la solicitud o la postulación ya fue resuelta.", "danger")

    # Volvemos exactamente a la misma pantalla del detalle de la clase para ver el cambio reflejado
    return redirect(url_for("clases.ver_detalle_admin", clase_id=clase_id))

# RUTAS DE PROFESOR PARA LAS CLASES
@bp.route("/mis-postulaciones/disponibles", methods=["GET"])
@requiere_rol(['PROFESOR'])
def ver_clases_para_postularse():
    
    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesión para ver tus postulaciones.", "warning")
        return redirect(url_for('auth.login'))
        
    profesor_id = user_id

    # Control de errores de la base de datos
    try:
        clases_disponibles = obtener_clases_disponibles_para_profesor(profesor_id)
    except Exception as e:
        # Evitamos la pantalla de error 500, capturando la falla
        flash("Ocurrió un error al recuperar el listado de clases disponibles.", "danger")
        clases_disponibles = []
    
    return render_template(
        "profesor/clases_disponibles.html",
        clases=clases_disponibles
    )


@bp.route("/mis-postulaciones/postularse", methods=["POST"])
@requiere_rol(['PROFESOR'])  
def postularse():
    from src.core.usuarios import conseguir_administrativos, obtener_usuario_por_id_core
    from src.core.clases import profesor_tiene_conflicto_horario
    profesor_id = session.get('usuario_id')
    
    # Leemos el string que viene del formulario
    clases_ids_raw = request.form.get("clases_ids")
    if not clases_ids_raw:
        flash("No se seleccionaron clases válidas.", "danger")
        return redirect(url_for("clases.ver_clases_para_postularse"))
    
    try:
        lista_ids = []
        for id_clase in clases_ids_raw.split(","):
            cleaned_id = id_clase.strip()
            if cleaned_id.isdigit():  
                lista_ids.append(int(cleaned_id))
        
        if not lista_ids:
            flash("El formato de las clases seleccionadas no es válido.", "danger")
            return redirect(url_for("clases.ver_clases_para_postularse"))

        for clase_id in lista_ids:
            # Validamos existencia de la clase
            clase_existe = db.session.get(Clase, clase_id)
            if not clase_existe:
                flash(f"La clase con ID {clase_id} no existe o ya no está disponible.", "warning")
                db.session.rollback()  
                return redirect(url_for("clases.ver_clases_para_postularse"))
            
            query_existente = select(PostulacionClase).where(
                PostulacionClase.clase_id == clase_id,
                PostulacionClase.profesor_id == profesor_id
            )
            postulacion_existente = db.session.scalar(query_existente)
            
            if postulacion_existente:
                flash("Ya te encontrás postulado a una de las clases seleccionadas.", "warning")
                db.session.rollback()
                return redirect(url_for("clases.ver_clases_para_postularse"))
            
            conflicto_horario = profesor_tiene_conflicto_horario (clase_id, profesor_id)
            print (conflicto_horario)
            if conflicto_horario:
                db.session.rollback()
                flash (f"El profesor ya tiene una clase en el mismo horario: {conflicto_horario}", "warning")
                return redirect(url_for("clases.ver_clases_para_postularse"))

            # Creamos la postulación vinculándola al ID correspondiente
            nueva_postulacion = PostulacionClase(
                clase_id=clase_id,
                profesor_id=profesor_id,
                estado="PENDIENTE"
            )
            db.session.add(nueva_postulacion)
            usuario = obtener_usuario_por_id_core(profesor_id)
        enviar_notificaciones(conseguir_administrativos(), "Nueva postulación", f"Se ha recibido una nueva postulación: {usuario.nombre}, {usuario.apellido} se ha anotado a la clase {clase_existe.nombre}. Para más información revise la casilla de clases", TipoNotificacion.NUEVA_APELACION_A_CLASE)
        
        db.session.commit()
        flash("Usted fue asignado correctamente, puede ver sus clases en la seccion 'Mis clases'.", "success")

    except Exception as e:
        db.session.rollback()
        # Esto te va a mostrar en la terminal si llega a saltar otra cosa de la base de datos
        print(f"❌ Error crítico en postulación: {e}") 
        flash("Hubo un error interno al procesar la postulación. Intentalo de nuevo.", "danger")
        
    return redirect(url_for("clases.ver_clases_para_postularse"))


@bp.route("/mis-postulaciones", methods=["GET"])
@requiere_rol(['PROFESOR']) 
def ver_mis_postulaciones():

    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesión para ver tus postulaciones.", "warning")
        return redirect(url_for('auth.login'))
        
    profesor_id = user_id
    
    try:
        postulaciones = obtener_postulaciones_de_profesor(profesor_id)
    except Exception as e:
        # Capturamos cualquier fallo de la base de datos (caída de servidor, error de sintaxis, etc.)
        # para que la aplicación no lance un error 500 al cliente.
        flash("Ocurrió un error al cargar tus postulaciones. Por favor, intenta de nuevo más tarde.", "danger")
        postulaciones = []  # Enviamos una lista vacía para que el template no rompa al iterar
    
    return render_template(
        "profesor/mis_postulaciones.html",
        postulaciones=postulaciones
    )

@bp.get("/mis-clases")
@requiere_rol(['PROFESOR']) 
def ver_clases_asignadas():
    """Ruta para que el profesor vea su agenda de clases asignadas (tabla dicta)."""
    
    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesión para ver tu agenda de clases.", "warning")
        return redirect(url_for('auth.login'))
    
    usuario_id = user_id 
    
    try:
        # Delegar al Core la búsqueda de las clases que dicta en la tabla 'dicta'
        clases_dictadas = obtener_clases_dictadas_por_profesor(usuario_id)
    except Exception as e:
        # Si falla la base de datos (por ejemplo, error en el JOIN de la tabla 'dicta'), 
        # atrapamos el error para evitar un error 500 y devolvemos una lista vacía de forma segura.
        flash("Ocurrió un error al cargar tu agenda de clases. Inténtalo de nuevo más tarde.", "danger")
        clases_dictadas = []

    return render_template(
        "profesor/mis_clases.html",
        clases=clases_dictadas,
        current_path=request.path
    )

@bp.route('/profesor/proponer', methods=['GET'])
@requiere_rol(['PROFESOR'])
def proponer_clase_vista():
    from src.core.salas import listar_salas_habilitadas
    from src.core.usuarios.usuarios import Usuario # 👈 Importamos el modelo para la relación
    
    """
    Renderiza el formulario para que el profesor proponga un espacio horario,
    limitando la selección únicamente a su especialidad asignada.
    """
    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect(url_for('auth.login'))

    # 1. Buscamos al profesor logueado junto con su especialidad asignada
    profesor = db.session.scalar(
        select(Usuario)
        .where(Usuario.id == user_id)
    )

    # Validación de seguridad por si no tiene configurada la especialidad en la BD
    if not profesor or not profesor.especialidad:
        flash("Tu usuario no tiene una especialidad asignada. Contactá al administrador.", "danger")
        return redirect(url_for('dashboard')) # O tu vista del home del profesor

    # 2. En lugar de listar todas, armamos la lista únicamente con SU especialidad
    # De esta manera, el bucle for del HTML funciona idéntico pero con una sola opción
    especialidades_profesor = [profesor.especialidad]
    
    salas = listar_salas_habilitadas()

    # 3. Renderizamos pasando las variables que el HTML y el JS modularizado esperan
    return render_template(
        'clases/proponer_clase.html',
        templates_especialidades=especialidades_profesor, # 👈 Modificado de forma segura
        puertas_salas=salas,
        dias_no_laborables=[] # Pasamos array vacío por defecto para que Flatpickr no pinche
    )

@bp.route('/proponer', methods=['POST'])
@requiere_rol(['PROFESOR']) 
def proponer_clase_post():
    """
    Ataja el formulario enviado por un profesor para proponer una nueva clase.
    """
    # 1. Identificación segura del Profesor desde la sesión
    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesión para proponer una clase.", "warning")
        return redirect(url_for('auth.login'))
    
    profesor_id = user_id

    # 2. Extracción de datos desde el HTML
    nombre = request.form.get('nombre')
    especialidad_id_str = request.form.get('especialidad_id')
    fecha_str = request.form.get('fecha_clase')
    horario_str = request.form.get('horario')
    duracion_str = request.form.get('duracion')
    descripcion = request.form.get('descripcion')
    sala_id_str = request.form.get('sala_id')

    # 3. Conversión de tipos y validaciones de negocio
    try:
        fecha_clase = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        horario = datetime.strptime(horario_str, '%H:%M').time()
        duracion = int(duracion_str)
        sala_id = int(sala_id_str)

        # Candado de fechas pasadas
        if fecha_clase <= datetime.now().date():
            flash('La fecha de la propuesta debe ser a partir de mañana.', 'danger')
            return redirect(url_for('clases.proponer_clase_vista'))

        # Evitar fines de semana
        if fecha_clase.weekday() in [5, 6]: 
            flash('No se pueden proponer clases para los fines de semana.', 'danger')
            return redirect(url_for('clases.proponer_clase_vista'))
        
        # Extracción segura del nombre de la Especialidad desde el Core
        especialidades_mock = listar_especialidades_activas()
        especialidad_nombre = "General" 

        for esp in especialidades_mock:       
            if str(esp.id) == str(especialidad_id_str).strip():
                if hasattr(esp.nombre, 'value'):
                    especialidad_nombre = esp.nombre.value
                else:
                    especialidad_nombre = esp.nombre
                break

        sala_elegida = obtener_sala(sala_id)
        if not sala_elegida:
            flash('La sala seleccionada no es válida.', 'danger')
            return redirect(url_for('clases.proponer_clase_vista'))

    except (ValueError, TypeError):
        flash('Error en el formato de los datos obligatorios.', 'danger')
        return redirect(url_for('clases.proponer_clase_vista'))
    
    propuesta_duplicada = db.session.scalar(
        select(Clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .where(
            ProfesorDictaClase.id_profesor == user_id,
            Clase.fecha_clase == fecha_clase,
            Clase.horario == horario,
            Clase.especialidad == especialidad_nombre,
            Clase.aprobada == False,
            Clase.suspendida == False,
            Clase.sala_id == sala_id
        )
    )

    if propuesta_duplicada:
        flash("Ya enviaste una propuesta exactamente para esa fecha y horario. Está pendiente de revisión.", "warning")
        return redirect(url_for('clases.historial_propuestas_profesor'))

    # 4. Delegación al Core pasando el ID del profesor proponent
    exito = proponer_clase_profesor(
        profesor_id=profesor_id,
        nombre=nombre,
        especialidad=especialidad_nombre,
        fecha_clase=fecha_clase,
        horario=horario,
        duracion=duracion,
        descripcion=descripcion,
        sala_id=sala_id
    )

    if exito:
        flash("Tu propuesta de clase fue enviada con éxito. Queda sujeta a aprobación de la administración.", "success")
        return redirect(url_for('clases.historial_propuestas_profesor'))
    else:
        flash('No se pudo registrar la propuesta. Verifique la disponibilidad horaria en su agenda.', 'danger')
        return redirect(url_for('clases.proponer_clase_vista'))
    
@bp.route('/admin/propuestas', methods=['GET'])
@requiere_rol(['ADMINISTRADOR'])
def listar_propuestas_pendientes():
    """
    Muestra al administrador las clases propuestas por profesores que aún no se aprobaron.
    """
    hoy = datetime.now().date()
    # Buscamos clases que no estén aprobadas y que tampoco estén suspendidas/canceladas
    query = select(Clase).where(
        Clase.aprobada == False,
        Clase.suspendida == False,
        Clase.fecha_clase > hoy
    ).order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    
    propuestas = db.session.scalars(query).all()
    
    return render_template('clases/panel_propuestas.html', propuestas=propuestas)

@bp.route('/admin/propuestas/revisar/<int:clase_id>', methods=['GET'])
@requiere_rol(['ADMINISTRADOR'])
def revisar_propuesta_vista(clase_id):
    """
    Abre el formulario de creación pre-operado con los datos de la propuesta.
    """
    propuesta = db.session.get(Clase, clase_id)
    if not propuesta or propuesta.aprobada:
        flash("La propuesta no existe o ya fue procesada.", "warning")
        return redirect(url_for('clases.listar_propuestas_pendientes'))

    # Traemos la infraestructura habitual para los selectores
    especialidades = listar_especialidades_activas()
    
    salas = listar_salas_habilitadas()

    return render_template(
        'clases/revisar_propuesta.html',
        propuesta=propuesta,
        templates_especialidades=especialidades,
        puertas_salas=salas,
        dias_no_laborables=[]
    )

@bp.route('/admin/propuestas/procesar/<int:clase_id>', methods=['POST'])
@requiere_rol(['ADMINISTRADOR'])
def procesar_propuesta_post(clase_id):
    from src.core.clases import _limpiar_propuestas_por_colision
    from src.core.clases import validar_disponibilidad_extendida

    """
    Procesa la propuesta del profesor de manera atómica y segura contra condiciones de carrera.
    El administrador únicamente puede alterar el tipo de clase (Fija o Individual).
    """
    propuesta = db.session.get(Clase, clase_id)
    if not propuesta:
        flash("La propuesta seleccionada no existe.", "danger")
        return redirect(url_for('clases.listar_propuestas_pendientes'))

    # El administrador SOLO define el Tipo de Clase desde el formulario
    tipo_clase = request.form.get('tipo_clase')
    if tipo_clase not in ["Fija", "Individual"]:
        flash('El tipo de clase seleccionado no es válido.', 'danger')
        return redirect(url_for('clases.revisar_propuesta_vista', clase_id=clase_id))

    # --- 🛡️ CONTROL DE CONCURRENCIA (ÚLTIMO SEGUNDO) ---
    disponible, fecha_conflicto = validar_disponibilidad_extendida(
        db.session, Clase, propuesta.sala_id, propuesta.fecha_clase, 
        propuesta.horario, propuesta.duracion, tipo_clase
    )

    if not disponible:
        try:
            if tipo_clase == "Individual":
                # Si colisiona de forma individual, no hay segundas oportunidades: se suspende.
                propuesta.suspendida = True 
                db.session.commit()
                flash("No se pudo procesar: La sala se encuentra ocupada en ese horario.", "danger")
                return redirect(url_for('clases.listar_propuestas_pendientes'))
            
            else:
                # 🔄 NUEVO COMPORTAMIENTO PARA FIJAS: No alteramos el estado en BD.
                # Devolvemos al Admin a la vista de la propuesta para que intente consolidarla como Individual.
                msg = f"La sala se ocupó el día {fecha_conflicto.strftime('%d/%m/%Y')} en ese horario. Podés aprobarla como una clase Individual únicamente."
                flash(f"No se pudo consolidar como Fija: {msg}", "warning")
                return redirect(url_for('clases.revisar_propuesta_vista', clase_id=clase_id))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al manejar conflicto de propuesta: {str(e)}")
            flash("Error interno al procesar el conflicto de agenda.", "danger")
            return redirect(url_for('clases.listar_propuestas_pendientes'))

    # --- FLUJO DE APROBACIÓN ---
    
    if tipo_clase == "Fija":
        try:
            relacion_original = db.session.scalar(
                select(ProfesorDictaClase).where(ProfesorDictaClase.id_clase == propuesta.id)
            )
            if not relacion_original:
                flash("No se encontró un profesor asociado a esta propuesta original.", "danger")
                return redirect(url_for('clases.revisar_propuesta_vista', clase_id=clase_id))
            
            # Resguardamos el ID del profesor para usarlo después en la expansión
            profesor_id = relacion_original.id_profesor

            # Resguardamos los parámetros limpios del objeto antes de su remoción física
            esp_nombre = propuesta.especialidad   
                     
            datos_clase = {
                "nombre": propuesta.nombre,
                "especialidad": esp_nombre,
                "tipo": tipo_clase,
                "fecha_clase": propuesta.fecha_clase,
                "horario": propuesta.horario,
                "duracion": propuesta.duracion,
                "descripcion": propuesta.descripcion,
                "sala_id": propuesta.sala_id
            }

            db.session.delete(relacion_original)
            db.session.delete(propuesta)
            db.session.flush() # Sincroniza remoción en memoria antes de expandir
            
            if crear_clases_agenda(id_profesor=profesor_id, **datos_clase):
                # El Core internamente ejecuta el commit si todo sale bien
                flash("La propuesta fue consolidada y expandida como Clase Fija hasta fin de mes.", "success")
            else:
                db.session.rollback()
                flash("No se pudieron generar las instancias de la clase fija.", "danger")
                return redirect(url_for('clases.revisar_propuesta_vista', clase_id=clase_id))
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en conversión Fija: {str(e)}")
            flash("Error interno al procesar la conversión de la clase.", "danger")
            return redirect(url_for('clases.revisar_propuesta_vista', clase_id=clase_id))

    else:
        # Individual: Consolidamos el mismo registro sin destruirlo
        try:
            propuesta.tipo = "Individual"
            propuesta.aprobada = True 
            
            _limpiar_propuestas_por_colision(propuesta) # Limpia baches competidores
            
            db.session.commit()
            flash("La propuesta de clase individual fue aprobada con éxito.", "success")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en aprobación Individual: {str(e)}")
            flash("Error al actualizar la propuesta individual en la base de datos.", "danger")
            return redirect(url_for('clases.revisar_propuesta_vista', clase_id=clase_id))

    return redirect(url_for('clases.listar_propuestas_pendientes'))

@bp.route('/profesor/historial', methods=['GET'])
@requiere_rol(['PROFESOR'])
def historial_propuestas_profesor():
    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesión para acceder.", "warning")
        return redirect(url_for('auth.login'))
        
    hoy = date.today()

    # Query robusta cruzando la intermedia y aplicando las reglas de negocio
    propuestas_pendientes = db.session.scalars(
        select(Clase)
        .join(ProfesorDictaClase, Clase.id == ProfesorDictaClase.id_clase)
        .where(
            ProfesorDictaClase.id_profesor == user_id,
            Clase.aprobada == False,
            Clase.suspendida == False,       # No suspendidas
            Clase.fecha_clase > hoy          # Estrictamente mayor a hoy (futuras)
        )
        .order_by(Clase.fecha_clase.asc(), Clase.horario.asc())
    ).all()

    return render_template(
        'clases/historial_propuesta_profesor.html',
        propuestas=propuestas_pendientes
    )