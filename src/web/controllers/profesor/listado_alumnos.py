from flask import render_template, session, request, flash, redirect, url_for

from src.core.clases import profesor_está_en_clase
from src.core.usuarios import tiene_alumnos, conseguir_lista_alumnos_clase_actual

def consultar_listado_alumnos ():

    # id_profesor = session.get("id")

    id_profesor = 15

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))

    # Comprobación 2: el profesor está en una clase [EN BD]
    if not profesor_está_en_clase (id_profesor):
        flash ("El profesor no se encuentra en una clase", 'warning')
        return redirect(url_for("profesor.index_profesor"))

    # Comprobación 3: lista vacía [EN BD]
    if not (tiene_alumnos(id_profesor, en_clase_actual=True)):
        flash ("No se han encontrado resultados", "warning")
        return render_template ('profesor/listado_alumnos.html')

    print ("LA BÚSQUEDA QUE HICE ES DE", request.args.get("busqueda"))
    busqueda = request.args.get("busqueda")

    lista_de_alumnos = conseguir_lista_alumnos_clase_actual(id_profesor, filtro_nombre=busqueda)
    print (lista_de_alumnos)
    if (lista_de_alumnos == []):
        print("XDD")
        flash ("No se han encontrado resultados", "warning")
        return render_template ('profesor/listado_alumnos.html', busqueda=busqueda)

    return render_template ('profesor/listado_alumnos.html',
                        lista_de_alumnos=lista_de_alumnos,
                        busqueda=busqueda
                           )