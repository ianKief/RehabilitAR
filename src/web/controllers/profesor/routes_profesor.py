import os

from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.core.database import db
from src.core.clases.clases import PostulacionClase

from src.core.clases import obtener_clases_dictadas_por_profesor, obtener_clases_disponibles_para_profesor, obtener_postulaciones_de_profesor

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

profesor_bp = Blueprint('profesor', __name__, url_prefix="/profesor", template_folder=TEMPLATE_DIR)

@profesor_bp.route("/mis-postulaciones/disponibles", methods=["GET"])
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


@profesor_bp.route("/mis-postulaciones/postularse", methods=["POST"])
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
    return redirect(url_for("profesor.ver_clases_para_postularse"))


@profesor_bp.route("/mis-postulaciones", methods=["GET"])
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


@profesor_bp.get("/mis-clases")
def ver_clases_asignadas():
    """Ruta para que el profesor vea su agenda de clases asignadas (tabla dicta)."""
    
    # 🕵️ MOCK: Forzamos el ID de profesor en 2 para pruebas locales de Pentabyte LABS
    usuario_id = 2 
    
    # 2. 🔍 Delegar al Core la búsqueda de las clases que dicta
    # (Esta es la función que va a hacer los joins con Clase y Sala)
    clases_dictadas = obtener_clases_dictadas_por_profesor(usuario_id)

    # 3. 📊 Renderizar la vista enviando los datos limpios
    return render_template(
        "profesor/mis_clases.html",
        clases=clases_dictadas,
        current_path=request.path
    )