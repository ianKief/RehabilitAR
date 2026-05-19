from flask import render_template, session, redirect, url_for, flash
from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.getClaseActual import getClaseActual

def renderizar_index_profesor ():

    dni_profesor = session.get("dni")

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))
    
    return render_template('/profesor/index.html', clase_actual = getClaseActual (dni_profesor))