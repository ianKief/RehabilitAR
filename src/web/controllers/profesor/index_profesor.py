from flask import render_template, session, redirect, url_for, flash
from src.core.clases import conseguir_clase_actual
from sqlalchemy.exc import MultipleResultsFound

from src.web.functions import devolver_hora_fin

def renderizar_index_profesor ():

    id_profesor = session.get("usuario_id")

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))
    
    try:
        datos = conseguir_clase_actual (id_profesor)

        if (datos == None):
            return render_template('/profesor/index.html') 
        clase_actual = datos[0]
        reservas = datos.reservas_totales
        asistencias = datos.asistencias_actuales
        return render_template('/profesor/index.html', clase_actual = clase_actual,
                               reservas = reservas, asistencias = asistencias,
                               hora_fin = devolver_hora_fin (clase_actual.horario, clase_actual.duracion)
                               )
    
    except ValueError as e: 
        flash(("Hay un error al obtener el valor:", str(e)), "danger")
    except MultipleResultsFound as e:
        flash(("Se ha encontrado más de una clase actual:", str(e)), "danger")
    return redirect(url_for('home'))