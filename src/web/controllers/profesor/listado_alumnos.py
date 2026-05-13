from flask import render_template, session, request

from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.conseguirListaAlumnos import conseguirListaAlumnos
from src.web.functions.filtrarPorNombre import filtrarPorNombre
from src.web.functions.tieneAlumnos import tieneAlumnos

def consultar_listado_alumnos ():

    dni_profesor = session.get("dni")
    rol_profesor = session.get("rol")

    # Comprobación 1: el profesor está logeado [EN SESIÓN]
    if not (rol_profesor == "profesor"):
        return render_template('index.html', error="El profesor debe estar logueado")

    # Comprobación 2: el profesor está en una clase [EN BD]
    if not profesorEstáEnClase (dni_profesor):
        return render_template('profesor/index.html', error="El profesor no se encuentra en una clase")

    # Comprobación 3: lista vacía
    if not (tieneAlumnos(dni_profesor)):
        return render_template ('profesor/listado_alumnos.html', error="No se han encontrado resultados")

    busqueda = request.args.get("busqueda")
    
    if (busqueda):
        lista_de_alumnos = filtrarPorNombre(busqueda, conseguirListaAlumnos(dni_profesor))
        if (lista_de_alumnos == []):
            return render_template ('profesor/listado_alumnos.html', error="No se han encontrado resultados")
    else:
        lista_de_alumnos = conseguirListaAlumnos(dni_profesor)

    return render_template ('profesor/listado_alumnos.html',
                        lista_de_alumnos=lista_de_alumnos
                           )