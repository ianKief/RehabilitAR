from flask import render_template, session, request, flash, url_for, redirect

from src.core.usuarios import tiene_alumnos
from src.core.reserva import conseguir_asistencias

from src.web.functions import agrupacion_manual_de_datos_de_comentarios_por_asistencia_y_alumno

def ver_comentarios_y_asistencias ():
    
    id_profesor = session.get("usuario_id")

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))

    # Comprobación 2: lista vacía
    if not (tiene_alumnos(id_profesor)):
        flash ("No se han encontrado resultados", "warning")
        return render_template ('profesor/ver_asistencias.html')

# Explicación de cómo HTML devuelve las variables:
# Búsqueda: si se deja vacío devuelve "", pero si no se especifica búsqueda (cosa que va a pasar cuando se cargue la página), devuelve None. A fin de uniformalizar, se establece un if debajo que cambie esto.
# Fecha: devuelve None si no se carga el formulario, "" en el otro caso, salvo si se inserta un dato, para el cual el formato será "YYYY-MM-DD"
# solo_comentarios: devuelve None o "", pero es suficiente para traducirlo a True o False
# estado: devuelve el valor del campo value seleccionado. Por default devuelve "seleccionar_todos", pero con el filtro puede devolver "presente" o "ausente"
    
    busqueda = request.args.get("busqueda")
    if busqueda == None:
        busqueda = ""
    fecha = request.args.get("fecha")
    if fecha == None:
        fecha = ""
    solo_comentarios = request.args.get("solo_comentarios") is not None
    estado = request.args.get(
        "estado"
    )
    if (estado == None):
        estado="seleccionar_todos"

    hay_filtro = busqueda!="" or fecha!="" or solo_comentarios==True or estado != "seleccionar_todos"

    # NOTA: Si en algún momento se aplican las FK y relationships adecuadas, puede quitarse la función de nombre largo
    lista_de_asistencias = agrupacion_manual_de_datos_de_comentarios_por_asistencia_y_alumno(conseguir_asistencias(id_profesor,
        busqueda=busqueda,
        estado=estado,
        fecha=fecha,
        solo_comentarios=solo_comentarios))
    
    return render_template ('profesor/ver_asistencias.html', lista_de_asistencias=lista_de_asistencias,
                                                                                    busqueda=busqueda,
                                                                                    fecha=fecha,
                                                                                    solo_comentarios=solo_comentarios,
                                                                                    hay_filtro=hay_filtro,
                                                                                    estado=estado)
