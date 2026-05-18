from flask import render_template, request, session

from src.web.functions.perteneceASuClase import perteneceASuClase
from src.web.functions.esDNI import esDNI
from src.web.functions.conseguirNombre import conseguirNombre
from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.alumnoTieneAsistencia import alumnoTieneAsistencia

def registrar_asistencia_manual ():

    dni_alumno = request.form.get('dni')
    dni_profesor = session.get("dni")

    if request.method == 'GET':
    
        print (session.get("rol"))

        # Comprobación 1: el profesor está logeado [EN SESIÓN]
    # COMPROBAR LOGIN
    #    return render_template('home.html', error="El profesor debe estar logueado")

        # Comprobación 2: el profesor está en una clase [EN BD]
        if not profesorEstáEnClase (dni_profesor):
            return render_template('profesor/index.html', error="El profesor no se encuentra en una clase")

        # Cargar formulario de presente
        return render_template('profesor/presente_manual.html')
    
    elif request.method == 'POST':

        # Comprobación 1: el profesor está logeado [EN SESIÓN]
    # COMPROBAR LOGIN
    #    return render_template('home.html', error="El profesor debe estar logueado")
        
        # Comprobación 2: el profesor está en una clase [EN BD]
        if not profesorEstáEnClase (dni_profesor):
            return render_template('profesor/index.html', error="El profesor no se encuentra en una clase")
        
        # Comprobación 3: se ha ingresado el DNI [EN CLIENTE]
        if not dni_alumno:
            return render_template('profesor/presente_manual.html', error="Debe ingresarse un DNI")
    
        # Comprobación 4: no se ha ingresado un DNI [EN CLIENTE]
        if not esDNI(dni_alumno):
            return render_template('profesor/presente_manual.html', error="El dato ingresado no es un DNI")

        # Comprobación 5: el alumno de ese DNI pertenece a esa clase [EN BD]
        if not perteneceASuClase (dni_profesor, dni_alumno):
                return render_template('profesor/presente_manual.html', error="El DNI del alumno no corresponde a la clase del profesor o no existe")

        # Comprobación 6: el alumno aún no tiene la asistencia de su clase [EN BD]
        if alumnoTieneAsistencia (dni_alumno):
                return render_template('profesor/presente_manual.html', error="El alumno ya tiene su asistencia marcada")

        # Registrar presente
        return render_template('/profesor/index.html', exito=True, nombre = conseguirNombre(dni_alumno), profesor_en_clase = True)