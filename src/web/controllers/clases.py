from datetime import datetime
from src.core.database import db
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from src.core.clases import crear_clases_agenda, listar_clases, listar_especialidades_activas, obtener_clase_por_id, obtener_horarios_disponibles, obtener_postulantes_clase, resolver_postulacion_clase
from src.core.salas import listar_salas_habilitadas, obtener_sala
from src.core.clases.clases import PostulacionClase
from src.core.clases import obtener_clases_dictadas_por_profesor, obtener_clases_disponibles_para_profesor, obtener_postulaciones_de_profesor

bp = Blueprint("clases", __name__, url_prefix="/clases")

@bp.get("/admin")
def listar_clases_admin():
    """Ruta que muestra el listado de clases para el administrador."""
    clases_registradas = listar_clases()
    return render_template("clases/clases_creadas.html", clases=clases_registradas, current_path=request.path)

@bp.get("/admin/<int:clase_id>")
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
    capacidad_str = request.form.get('capacidad_maxima')
    descripcion = request.form.get('descripcion')
    sala_id_str = request.form.get('sala_id')

    # 2. Conversión de tipos y formatos de datos
    try:
        fecha_clase = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        horario = datetime.strptime(horario_str, '%H:%M').time()
        duracion = int(duracion_str)
        capacidad_maxima = int(capacidad_str)
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
                # 🔄 CAMBIO CLAVE: Si es un objeto Enum, extraemos su .value ("TREN SUPERIOR")
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

        if capacidad_maxima > sala_elegida.capacidad:
            flash(f'Error: La capacidad máxima para esta clase supera el límite físico de la Sala {sala_elegida.numero_puerta} (Máximo: {sala_elegida.capacidad} personas).', 'danger')
            return redirect(url_for('clases.nueva_clase'))

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
        capacidad_maxima=capacidad_maxima,
        descripcion=descripcion,
        sala_id=sala_id
    )

    if exito:
        flash('Clase(s) programada(s) con éxito para el mes en curso.', 'success')
    else:
        flash('No se pudieron programar clases (las fechas calculadas ya pasaron).', 'warning')

    return redirect(url_for('clases.listar_clases_admin'))


@bp.post("/admin/postulacion/<int:postu_id>/<string:accion>")
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

    # 3. Delegar la transacción al Core
    exito = resolver_postulacion_clase(postu_id, accion)

    # 4. Mensajes Flash basados en el resultado de la operación
    if exito:
        if accion == "aceptar":
            flash("¡Postulación aceptada con éxito! El profesor fue asignado y se liberó la cartelera.", "success")
        else:
            flash("La postulación ha sido rechazada correctamente.", "info")
    else:
        flash("Hubo un error al procesar la solicitud o la postulación ya fue resuelta.", "danger")

    # 5. Volvemos exactamente a la misma pantalla del detalle de la clase para ver el cambio reflejado
    return redirect(url_for("clases.ver_detalle_admin", clase_id=clase_id))

# RUTAS DE PROFESOR PARA LAS CLASES
@bp.route("/mis-postulaciones/disponibles", methods=["GET"])
# @login_required
def ver_clases_para_postularse():
    # Simulamos el ID del profesor logueado temporalmente si no tenés la sesión lista
    # En producción usarías: profesor_id = current_user.id
    profesor_id = 2 
    
    # Validar que el usuario sea efectivamente un profesor (seguridad de roles)
    # if current_user.rol != 'Profesor': abort(403)

    clases_disponibles = obtener_clases_disponibles_para_profesor(profesor_id)
    
    return render_template(
        "profesor/clases_disponibles.html",
        clases=clases_disponibles
    )


@bp.route("/mis-postulaciones/postularse", methods=["POST"])
# @login_required
def postularse():
    # Simulamos el ID del profesor logueado de momento
    profesor_id = 2 
    
    # 1. Capturamos el string de IDs que viene del input oculto ("14,15,16")
    clases_ids_raw = request.form.get("clases_ids")
    
    if not clases_ids_raw:
        flash("No se seleccionaron clases válidas.", "danger") # Descomentá si usás flash messages
        return redirect(url_for("profesor.ver_clases_para_postularse"))
    
    try:
        # 2. Convertimos "14,15,16" en una lista de Python real: [14, 15, 16]
        lista_ids = [int(id_clase) for id_clase in clases_ids_raw.split(",")]
        
        # 3. Insertamos un registro PENDIENTE por cada instancia del bloque
        for clase_id in lista_ids:
            nueva_postulacion = PostulacionClase(
                clase_id=clase_id,
                profesor_id=profesor_id,
                estado="PENDIENTE" # Nace como pendiente para que el admin lo decida
            )
            db.session.add(nueva_postulacion)
        
        # 4. Impactamos la base de datos de un solo tiro
        db.session.commit()
        flash("¡Postulación enviada con éxito para todo el bloque!", "success")

    except Exception as e:
        db.session.rollback()
        flash("Hubo un error al procesar la postulación.", "danger")
        print(f"Error en postulación: {e}") # Para debuggear en consola
        
    # 5. Redirigimos de vuelta a la cartelera (que ahora ya no va a mostrar estas clases)
    return redirect(url_for("clases.ver_clases_para_postularse"))


@bp.route("/mis-postulaciones", methods=["GET"])
# @login_required
def ver_mis_postulaciones():
    # Seguimos simulando el ID 2 del profesor con el que venimos probando exitosamente
    profesor_id = 2 
    
    # Obtenemos los bloques ya formateados y agrupados
    postulaciones = obtener_postulaciones_de_profesor(profesor_id)
    
    return render_template(
        "profesor/mis_postulaciones.html",
        postulaciones=postulaciones
    )

@bp.get("/mis-clases")
def ver_clases_asignadas():
    """Ruta para que el profesor vea su agenda de clases asignadas (tabla dicta)."""
    
    # MOCK: Forzamos el ID de profesor en 2 para pruebas locales
    usuario_id = 2 
    
    # 2. Delegar al Core la búsqueda de las clases que dicta
    clases_dictadas = obtener_clases_dictadas_por_profesor(usuario_id)

    return render_template(
        "profesor/mis_clases.html",
        clases=clases_dictadas,
        current_path=request.path
    )