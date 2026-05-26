from datetime import datetime
from src.core.database import db
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from src.core.clases import crear_clases_agenda, listar_clases, listar_especialidades_activas, listar_salas_habilitadas, obtener_clase_por_id, obtener_horarios_disponibles, obtener_postulantes_clase, obtener_sala_por_id

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
 # Asegurate de tener estas importaciones

@bp.route('/crear', methods=['POST'])
def crear_clase_post():
    """
    Ataja el formulario por POST, adapta los nombres de los campos
    a las columnas reales del modelo 'Clase' y limpia los tipos de datos.
    """
    # 1. Extracción de datos desde el HTML (buscando por el atributo 'name')
    nombre = request.form.get('nombre')
    especialidad_id_str = request.form.get('especialidad_id')
    tipo_clase = request.form.get('tipo_clase') # En el HTML se llama tipo_clase
    fecha_str = request.form.get('fecha_clase')
    horario_str = request.form.get('horario')
    duracion_str = request.form.get('duracion')
    capacidad_str = request.form.get('capacidad_maxima')
    descripcion = request.form.get('descripcion')
    sala_id_str = request.form.get('sala_id') # Recibe el número del select

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
        if fecha_clase.weekday() in [5, 6]: # evita que se elijan sabados o domingos del lado del back
            flash('No se pueden programar clases los fines de semana.', 'danger')
            return redirect(url_for('clases.nueva_clase'))
        
        especialidades_mock = listar_especialidades_activas()
        especialidad_nombre = "General" 
        for esp in especialidades_mock:       
            if str(esp.id) == especialidad_id_str:
                especialidad_nombre = esp.nombre
                break
        
        sala_elegida = obtener_sala_por_id(sala_id)
        if not sala_elegida:
            flash('La sala seleccionada no es válida.', 'danger')
            return redirect(url_for('clases.nueva_clase'))

        if capacidad_maxima > sala_elegida.capacidad:
            flash(f'Error: La capacidad máxima para esta clase supera el límite físico de la Sala {sala_elegida.numero_puerta} (Máximo: {sala_elegida.capacidad} personas).', 'danger')
            return redirect(url_for('clases.nueva_clase'))

    except (ValueError, TypeError) as e:
        flash('Error en el formato de los datos obligatorios.', 'danger')
        return redirect(url_for('clases.nueva_clase'))

    # 3. Envío de datos limpios al Core respetando tu modelo
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

from flask import redirect, url_for, flash, abort
from src.core.clases import resolver_postulacion_clase, obtener_clase_por_id

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