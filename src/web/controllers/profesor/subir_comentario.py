from flask import render_template, session, request, flash, url_for, redirect

from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.perteneceASuClase import perteneceASuClase
from src.web.functions.conseguirPerfilAlumno import conseguirPerfilAlumno
from src.web.functions.subirComentario import subirComentario


def subir_comentario_a_alumnoXclase (dni):
    dni_profesor = session.get("dni")
        
    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))

    # Comprobación 2: el profesor está en una clase [EN BD]
    if not profesorEstáEnClase (dni_profesor):
        flash ("El profesor no se encuentra en una clase", 'warning')
        return redirect(url_for("profesor.index_profesor"))
    
    # Comprobación 3: el alumno de ese DNI pertenece a esa clase [EN BD]
    if not perteneceASuClase (dni_profesor, dni):
        flash ("El DNI del alumno no corresponde a la clase actual del profesor o no existe", "warning")
        return redirect(url_for("profesor.listado_alumnos"))
    
    comentario = request.form.get("comentario")
    perfil_alumno = conseguirPerfilAlumno(dni)

    # Comprobación 4: el comentario tiene contenido [EN CLIENTE]
    if not comentario:
        flash ("El comentario no tiene contenido", "warning")
        return render_template('profesor/perfil_alumno.html', error="El comentario no tiene contenido", alumno=perfil_alumno)
    
    subirComentario (dni, comentario)

    flash ("Se ha subido el comentario exitosamente", "success")
    return render_template('profesor/perfil_alumno.html', alumno=perfil_alumno)   