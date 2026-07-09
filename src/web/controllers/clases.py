from datetime import datetime
from src.core.database import db
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from src.core.clases import crear_clases_agenda, listar_clases, listar_especialidades_activas, obtener_clase_por_id, obtener_horarios_disponibles, obtener_postulantes_clase, procesar_suspension_o_reactivacion, resolver_postulacion_clase
from src.core.salas import listar_salas_habilitadas, obtener_sala
from src.core.clases.clases import Clase, PostulacionClase, ProfesorDictaClase
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
    
    return render_template('clases/crear_clase.html', templates_especialidades=especialidades, puertas_salas=salas)

@bp.route('/api/horarios-disponibles', methods=['GET'])
def api_horarios_disponibles():
    fecha_str = request.args.get('fecha')
    duracion_str = request.args.get('duracion', '45') # Por defecto 45 min
    sala_id = request.args.get('sala_id')
    tipo_clase = request.args.get('tipo', 'Individual')

    if not fecha_str:
        return jsonify([]), 400

    try:
        fecha_evaluar = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        duracion = int(duracion_str)
        
        # Le pedimos la info al Core
        libres = obtener_horarios_disponibles(fecha_evaluar, duracion, int(sala_id), tipo_clase)
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
    from datetime import date
    
    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesión para postularte a las clases.", "warning")
        return redirect(url_for('auth.login'))
        
    # Como tu modelo Profesor usa el id de usuario como Primary Key (Herencia), 
    # el profesor_id que necesita la postulación es directamente el user_id de la sesión.
    profesor_id = user_id
    
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

        hoy = date.today()

        for clase_id in lista_ids:
            # 1. Validamos la existencia física de la clase en la BD
            clase_existe = db.session.get(Clase, clase_id)
            if not clase_existe:
                flash(f"La clase con ID {clase_id} no existe.", "warning")
                db.session.rollback()  
                return redirect(url_for("clases.ver_clases_para_postularse"))
            
            # 2. Validar que la clase no esté suspendida institucionalmente
            if clase_existe.suspendida:
                flash(f"No podés postularte a '{clase_existe.nombre}' porque está suspendida temporalmente.", "danger")
                db.session.rollback()
                return redirect(url_for("clases.ver_clases_para_postularse"))
                
            # Validar que la clase no pertenezca al pasado
            if clase_existe.fecha_clase < hoy:
                flash(f"No podés postularte a '{clase_existe.nombre}' porque ya pasó de fecha.", "danger")
                db.session.rollback()
                return redirect(url_for("clases.ver_clases_para_postularse"))

            # 4. Validar que la clase no tenga ya un profesor asignado ("dueño")
            query_asignacion = select(ProfesorDictaClase).where(ProfesorDictaClase.id_clase == clase_id)
            ya_asignada = db.session.scalar(query_asignacion)
            if ya_asignada:
                flash(f"La clase '{clase_existe.nombre}' ya tiene un profesor asignado.", "warning")
                db.session.rollback()
                return redirect(url_for("clases.ver_clases_para_postularse"))
            
            # 5. CORRECCIÓN DUPLICADOS: Buscamos si ya se postuló ignorando el historial "SUSPENDIDA"
            query_existente = select(PostulacionClase).where(
                PostulacionClase.clase_id == clase_id,
                PostulacionClase.profesor_id == profesor_id,
                PostulacionClase.estado.in_(["PENDIENTE", "ACEPTADA", "RECHAZADA"])
            )
            postulacion_existente = db.session.scalar(query_existente)
            
            if postulacion_existente:
                flash("Ya te encontrás postulado a una de las clases seleccionadas.", "warning")
                db.session.rollback()
                return redirect(url_for("clases.ver_clases_para_postularse"))

            # Creamos la postulación vinculándola al ID correspondiente en estado PENDIENTE
            nueva_postulacion = PostulacionClase(
                clase_id=clase_id,
                profesor_id=profesor_id,
                estado="PENDIENTE"
            )
            db.session.add(nueva_postulacion)
            
            usuario = obtener_usuario_por_id_core(profesor_id)
            enviar_notificaciones(
                conseguir_administrativos(), 
                "Nueva postulación", 
                f"Se ha recibido una nueva postulación: {usuario.nombre}, {usuario.apellido} se ha anotado a la clase {clase_existe.nombre}. Para más información revise la casilla de clases", 
                TipoNotificacion.NUEVA_APELACION_A_CLASE
            )
        
        db.session.commit()
        flash("Usted se ha postulado correctamente, puede ver el estado en la sección correspondientes.", "success")
        
    except Exception as e:
        db.session.rollback()
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

@bp.route("/<int:clase_id>/alternar-suspension", methods=["GET", "POST"])
@requiere_rol(['ADMINISTRADOR']) 
def alternar_suspension(clase_id):
    from src.core.clases.clases import tz_arg

    resultado = procesar_suspension_o_reactivacion(clase_id, tz_arg)
    
    # Se manda el flash dinámico según lo que devolvió el motor de servicios
    flash(resultado["message"], resultado["status"])
    
    return redirect(url_for("clases.ver_detalle_admin", clase_id=clase_id))