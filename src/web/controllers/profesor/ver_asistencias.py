from flask import render_template, session, request

from src.web.functions.tieneAlumnos import tieneAlumnos
from src.web.functions.conseguirTodasLasAsistenciasAlumnos import conseguirTodasLasAsistenciasAlumnos
from src.web.functions.filtrarAsistencias import filtrarAsistencias

def ver_comentarios_y_asistencias ():
    
    dni_profesor = session.get("dni")
    rol_profesor = session.get("rol")

    # Comprobación 1: el profesor está logeado [EN SESIÓN]
    if not (rol_profesor == "profesor"):
        return render_template('home.html', error="El profesor debe estar logueado")

    # Comprobación 2: lista vacía
    if not (tieneAlumnos(dni_profesor)):
        return render_template ('profesor/ver_asistencias.html', error="No se han encontrado resultados")

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

    print ("busqueda (tiene que ser distinta a ''):", busqueda)
    print ("Fecha (Tiene que ser distinta a ''):", fecha)
    print ("solo_comentarios (tiene que ser distinto a False):", solo_comentarios)
    print ("estado (tiene que ser distinto a 'seleccionar_todos'):", estado)

    hay_filtro = busqueda!="" or fecha!="" or solo_comentarios==True or estado != "seleccionar_todos"

    print ("HAY FILTRO", hay_filtro)

    return render_template ('profesor/ver_asistencias.html', lista_de_asistencias=filtrarAsistencias (conseguirTodasLasAsistenciasAlumnos(dni_profesor),
                                                                                           busqueda=busqueda,
                                                                                           estado=estado,
                                                                                           fecha=fecha,
                                                                                           solo_comentarios=solo_comentarios),
                                                                                    busqueda=busqueda,
                                                                                    fecha=fecha,
                                                                                    solo_comentarios=solo_comentarios,
                                                                                    hay_filtro=hay_filtro,
                                                                                    estado=estado)
# El método filtrarAsistencias es un archivo de pruebas. Una consulta directa a BD será brutalmente más eficaz y conciso.