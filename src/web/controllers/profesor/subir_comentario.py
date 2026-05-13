from flask import render_template, session, request

from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.perteneceASuClase import perteneceASuClase
from src.web.functions.conseguirPerfilAlumno import conseguirPerfilAlumno
from src.web.functions.subirComentario import subirComentario

def subir_comentario_alumnoXclase (dni):

    dni_profesor = session.get("dni")
    rol_profesor = session.get("rol")

    # Comprobación 1: el profesor está logeado [EN SESIÓN]
    if not (rol_profesor == "profesor"):
        return render_template('index.html', error="El profesor debe estar logueado")
        
    # Comprobación 2: el profesor está en una clase [EN BD]
    if not profesorEstáEnClase (dni_profesor):
        return render_template('profesor/index.html', error="El profesor no se encuentra en una clase")
    
    # Comprobación 3: el alumno de ese DNI pertenece a esa clase [EN BD]
    if not perteneceASuClase (dni_profesor, dni):
            return render_template('profesor/listado_alumnos.html', error="El DNI del alumno no corresponde a la clase actual del profesor o no existe")
    
    comentario = request.form.get("comentario")

    # Comprobación 4: el comentario tiene contenido
    if not comentario:
         return {"exito": False, "mensaje": "El comentario no tiene contenido"}
    
    subirComentario (dni, comentario)
    
    return {"exito": True, "mensaje": "Se ha subido el comentario exitosamente"}