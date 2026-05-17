from flask import Blueprint, render_template

#Blueprint 'clases'
clases_bp = Blueprint('clases', __name__)

@clases_bp.route('/crear-clase')
def mostrar_formulario():
    return render_template('crear_clase.html')