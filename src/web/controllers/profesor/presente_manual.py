from flask import render_template, request, session, flash, url_for, redirect

from src.core.clases import profesor_está_en_clase
from src.core.usuarios import alumno_pertenece_a_clase_actual_profesor
from src.core.asistencias import alumno_tiene_asistencia, registrar_presente_alumno
from src.web.functions import es_dni

from src.core.reservas import AsistenciaReserva

def registrar_asistencia_manual ():

    dni_alumno = request.form.get('dni')
    id_profesor = session.get("usuario_id")

    if request.method == 'GET':
    
        # Comprobación 1: el profesor está logeado [EN INSTANCIA]
        # COMPROBAR LOGIN
        #   flash('El profesor no está logueado', 'warning')
        #   return redirect(url_for('home'))

        # Comprobación 2: el profesor está en una clase [EN BD]
        if not profesor_está_en_clase (id_profesor):
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
        if not es_dni(dni_alumno):
            flash ("El dato ingresado no es un DNI", "warning")
            return render_template('profesor/presente_manual.html')
        
        # Comprobación 4: el profesor está en una clase [EN BD]
        if not profesor_está_en_clase (id_profesor):
            flash ("El profesor no se encuentra en una clase", 'warning')
            return redirect(url_for("profesor.index_profesor"))
        
        # Comprobación 5: el alumno de ese DNI pertenece a esa clase [EN BD]
        if not alumno_pertenece_a_clase_actual_profesor (id_profesor, dni_alumno):
            flash ("El DNI del alumno no corresponde a la clase del profesor o no existe", "warning")
            return render_template('profesor/presente_manual.html')

        estado_asistencia_alumno = alumno_tiene_asistencia (dni_alumno=dni_alumno)

        # Comprobación 5.5: caso que no debería existir porque se asume que es el único alumno perteneciente a la clase y que se va a conseguir True o False
        if estado_asistencia_alumno == None:
            flash("Ha ocurrido un error desconocido. Prueba de vuelta", "warning")

        # Comprobación 6: el alumno aún no tiene la asistencia de su clase [EN BD]
        if estado_asistencia_alumno == AsistenciaReserva.PRESENTE:
            flash ("El alumno ya tiene su asistencia marcada", "success")
            return render_template('profesor/presente_manual.html')

        # Comprobación 7: el alumno canceló su reserva (dado que no queremos comprometer los datos del cliente más de la cuenta, la interfaz es la misma a la de si no pertenece a la clase)
        if estado_asistencia_alumno == AsistenciaReserva.CANCELADA:
            flash ("El DNI del alumno no corresponde a la clase del profesor o no existe", "warning")
            return render_template('profesor/presente_manual.html')
        
        exito = registrar_presente_alumno (dni_alumno=dni_alumno)

        if not exito:
            flash ('Ha ocurrido un error inesperado', 'danger')
            return redirect(url_for("profesor.index_profesor"))
        
        flash ("Se ha registrado el presente exitosamente", "success")
        return redirect(url_for("profesor.index_profesor"))