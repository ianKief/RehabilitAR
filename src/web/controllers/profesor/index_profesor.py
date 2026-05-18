from flask import render_template, session
from src.web.functions.profesorEstáEnClase import profesorEstáEnClase

def renderizar_index_profesor ():

    dni_profesor = session.get("dni")

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #    return render_template('home.html', error="El profesor debe estar logueado")
    
    return render_template('/profesor/index.html', profesor_en_clase = profesorEstáEnClase (dni_profesor))