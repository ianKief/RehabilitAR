from flask import render_template, session, redirect, url_for, flash
from src.core.clases import conseguir_clase_actual

def renderizar_index_profesor ():

    id_profesor = session.get("id")

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))
    
    return render_template('/profesor/index.html', clase_actual = conseguir_clase_actual (id_profesor))