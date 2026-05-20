from flask import render_template, session, request, flash, redirect, url_for

from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.conseguirListaAlumnos import conseguirListaAlumnos
from src.web.functions.filtrarPorNombre import filtrarPorNombre
from src.web.functions.tieneAlumnos import tieneAlumnosEnClase

def consultar_listado_alumnos ():

    dni_profesor = session.get("dni")

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))

    # Comprobación 2: el profesor está en una clase [EN BD]
    if not profesorEstáEnClase (dni_profesor):
        flash ("El profesor no se encuentra en una clase", 'warning')
        return redirect(url_for("profesor.index_profesor"))

    # Comprobación 3: lista vacía [EN BD]
    if not (tieneAlumnosEnClase(dni_profesor)):
        flash ("No se han encontrado resultados", "warning")
        return render_template ('profesor/listado_alumnos.html')

    busqueda = request.args.get("busqueda")
    # esto tiene un error en el filtrado. Se verá luego de la integración con BD si se puede hacer andar.

    if (busqueda):
        lista_de_alumnos = filtrarPorNombre(busqueda, conseguirListaAlumnos(dni_profesor))
        if (lista_de_alumnos == []):
            flash ("No se han encontrado resultados", "warning")
            return render_template ('profesor/listado_alumnos.html', busqueda=busqueda)
    else:
        lista_de_alumnos = conseguirListaAlumnos(dni_profesor)

    return render_template ('profesor/listado_alumnos.html',
                        lista_de_alumnos=lista_de_alumnos,
                        busqueda=busqueda
                           )