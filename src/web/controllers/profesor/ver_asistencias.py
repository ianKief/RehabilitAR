from flask import render_template, session, request

from src.web.functions.tieneAlumnos import tieneAlumnos
from src.web.functions.conseguirTodasLasAsistenciasAlumnos import conseguirTodasLasAsistenciasAlumnos

def ver_comentarios_y_asistencias ():
    
    dni_profesor = session.get("dni")
    rol_profesor = session.get("rol")

    # Comprobación 1: el profesor está logeado [EN SESIÓN]
    if not (rol_profesor == "profesor"):
        return render_template('index.html', error="El profesor debe estar logueado")

    # Comprobación 2: lista vacía
    if not (tieneAlumnos(dni_profesor)):
        return render_template ('profesor/listado_alumnos.html', error="No se han encontrado resultados")

    return render_template ('profesor/ver_asistencias.html', conseguirTodasLasAsistenciasAlumnos(dni_profesor))