from flask import render_template, session, request
from flask import Blueprint
dev_bp = Blueprint('dev', __name__, url_prefix="/dev")

@dev_bp.route('/', methods=['GET', 'POST'])
def establecer_cookies_manual ():
    
    if request.method == "POST":

        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        dni = request.form.get("dni")
        rol = request.form.get("rol")

        session["nombre"] = nombre
        session["apellido"] = apellido
        session["dni"] = dni
        session["rol"] = rol

        print (session.get("rol"))

        return render_template('index.html')

    elif request.method == "GET":
        return render_template ('dev/altera_sesiones.html')

