from flask import render_template, session, request, flash, url_for, redirect

from src.core.clases import profesor_está_en_clase
from src.core.usuarios import alumno_pertenece_a_clase_actual_profesor
from src.core.reserva import subir_comentario

def subir_comentario_a_alumnoXclase (dni):
    id_profesor = session.get("id")

    comentario = request.form.get("comentario")

    # Comprobación 1: el comentario tiene contenido [EN CLIENTE]
    if not comentario:
        flash ("El comentario no tiene contenido", "warning")
        return redirect(url_for('profesor.perfil_alumno', dni=dni))
            
    # Comprobación 2: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))

    # Comprobación 3: el profesor está en una clase [EN BD]
    if not profesor_está_en_clase (id_profesor):
        flash ("El profesor no se encuentra en una clase", 'warning')
        return redirect(url_for("profesor.index_profesor"))
    
    # Comprobación 4: el alumno de ese DNI pertenece a esa clase [EN BD]
    if not alumno_pertenece_a_clase_actual_profesor (id_profesor, dni):
        flash ("El DNI del alumno no corresponde a la clase actual del profesor o no existe", "warning")
        return redirect(url_for("profesor.listado_alumnos"))
    
    subir_comentario (dni, comentario)

    flash ("Se ha subido el comentario exitosamente", "success")
    return redirect(url_for('profesor.perfil_alumno', dni=dni))
