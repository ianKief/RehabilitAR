from flask import render_template, request, session, flash, url_for, redirect

from src.web.functions.perteneceASuClase import perteneceASuClase
from src.web.functions.esDNI import esDNI
from src.web.functions.conseguirNombre import conseguirNombre
from src.web.functions.profesorEstáEnClase import profesorEstáEnClase
from src.web.functions.alumnoTieneAsistencia import alumnoTieneAsistencia
from src.web.functions.getClaseActual import getClaseActual

def registrar_asistencia_manual ():

    dni_alumno = request.form.get('dni')
    dni_profesor = session.get("dni")

    if request.method == 'GET':
    
        print (session.get("rol"))

        # Comprobación 1: el profesor está logeado [EN INSTANCIA]
        # COMPROBAR LOGIN
        #   flash('El profesor no está logueado', 'warning')
        #   return redirect(url_for('home'))

        # Comprobación 2: el profesor está en una clase [EN BD]
        if not profesorEstáEnClase (dni_profesor):
            flash ("El profesor no se encuentra en una clase", 'warning')
            return redirect(url_for("profesor.index_profesor"))

        # Cargar formulario de presente
        return render_template('profesor/presente_manual.html')
    
    elif request.method == 'POST':

        # Comprobación 1: se ha ingresado el DNI [EN CLIENTE]
        if not dni_alumno:
            flash ("Debe ingresarse un DNI", "warning")
            return render_template('profesor/presente_manual.html')
    
        # Comprobación 2: no se ha ingresado un DNI [EN CLIENTE]
        if not esDNI(dni_alumno):
            flash ("El dato ingresado no es un DNI", "warning")
            return render_template('profesor/presente_manual.html')

        # Comprobación 3: el profesor está logeado [EN INSTANCIA]
        # COMPROBAR LOGIN
        #   flash('El profesor no está logueado', 'warning')
        #   return redirect(url_for('home'))
        
        # Comprobación 4: el profesor está en una clase [EN BD]
        if not profesorEstáEnClase (dni_profesor):
            flash ("El profesor no se encuentra en una clase", 'warning')
            return redirect(url_for("profesor.index_profesor"))
        
        # Comprobación 5: el alumno de ese DNI pertenece a esa clase [EN BD]
        if not perteneceASuClase (dni_profesor, dni_alumno):
            flash ("El DNI del alumno no corresponde a la clase del profesor o no existe", "warning")
            return render_template('profesor/presente_manual.html')

        # Comprobación 6: el alumno aún no tiene la asistencia de su clase [EN BD]
        if alumnoTieneAsistencia (dni_alumno):
            flash ("El alumno ya tiene su asistencia marcada", "success")
            return render_template('profesor/presente_manual.html')

        # Registrar presente

        flash ("Se ha registrado el presente exitosamente", "success")
        return redirect(url_for("profesor.index_profesor"))