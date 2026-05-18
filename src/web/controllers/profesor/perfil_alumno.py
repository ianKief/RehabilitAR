from flask import render_template, session

from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.perteneceASuClase import perteneceASuClase
from src.web.functions.conseguirPerfilAlumno import conseguirPerfilAlumno

def cargar_perfil_alumno (dni):

    dni_profesor = session.get("dni")
    rol_profesor = session.get("rol")
    
    # Comprobación 1: el profesor está logeado [EN SESIÓN]
    if not (rol_profesor == "profesor"):
        return render_template('home.html', error="El profesor debe estar logueado")
        
    # Comprobación 2: el profesor está en una clase [EN BD]
    if not profesorEstáEnClase (dni_profesor):
        return render_template('profesor/index.html', error="El profesor no se encuentra en una clase")
    
    # Comprobación 3: el alumno de ese DNI pertenece a esa clase [EN BD]
    if not perteneceASuClase (dni_profesor, dni):
            return render_template('profesor/listado_alumnos.html', error="El DNI del alumno no corresponde a la clase del profesor o no existe")
        
    return render_template ('/profesor/perfil_alumno.html',
                            alumno=conseguirPerfilAlumno(dni)
                            )