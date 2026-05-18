from flask import render_template, session, request

from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.perteneceASuClase import perteneceASuClase
from src.web.functions.conseguirPerfilAlumno import conseguirPerfilAlumno
from src.web.functions.subirComentario import subirComentario


def subir_comentario_a_alumnoXclase (dni):
    print (dni)
    dni_profesor = session.get("dni")

    # Comprobación 1: el profesor está logeado [EN SESIÓN]
    # COMPROBAR LOGIN
    #    return render_template('home.html', error="El profesor debe estar logueado")
        
    # Comprobación 2: el profesor está en una clase [EN BD]
    if not profesorEstáEnClase (dni_profesor):
        return render_template('profesor/index.html', error="El profesor no se encuentra en una clase")
    
    # Comprobación 3: el alumno de ese DNI pertenece a esa clase [EN BD]
    if not perteneceASuClase (dni_profesor, dni):
            return render_template('profesor/listado_alumnos.html', error="El DNI del alumno no corresponde a la clase actual del profesor o no existe")
    
    comentario = request.form.get("comentario")
    perfil_alumno = conseguirPerfilAlumno(dni)

    # Comprobación 4: el comentario tiene contenido [EN CLIENTE]
    if not comentario:
         return render_template('profesor/perfil_alumno.html', error="El comentario no tiene contenido", alumno=perfil_alumno)
    
    subirComentario (dni, comentario)
    
    return render_template('profesor/perfil_alumno.html', exito=True, alumno=perfil_alumno)   