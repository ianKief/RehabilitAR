from flask import render_template, session
from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from flask import Blueprint
profesor_bp = Blueprint('profesor', __name__, url_prefix="/profesor")

@profesor_bp.route('/', methods=['GET'])

def renderizar_index_profesor ():

    dni_profesor = session.get("dni")
    rol_profesor = session.get("rol")

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    if not (rol_profesor == "profesor"):
        return render_template('index.html', error="El profesor debe estar logueado")
    
    return render_template('/profesor/index.html', profesor_en_clase = profesorEstáEnClase (dni_profesor))