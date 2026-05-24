from flask import render_template, session, flash, url_for, redirect

from src.core.clases import profesor_está_en_clase
from src.core.usuarios import alumno_pertenece_a_clase_actual_profesor, conseguir_perfil_alumno

def cargar_perfil_alumno (dni):

    id_profesor = session.get("usuario_id")

    # Comprobación 1: el profesor está logeado [EN INSTANCIA]
    # COMPROBAR LOGIN
    #   flash('El profesor no está logueado', 'warning')
    #   return redirect(url_for('home'))

    # Comprobación 2: el profesor está en una clase [EN BD]
    if not profesor_está_en_clase (id_profesor):
        flash ("El profesor no se encuentra en una clase", "warning")
        return redirect(url_for("profesor.index_profesor"))
    
    # Comprobación 3: el alumno de ese DNI pertenece a esa clase [EN BD]
    if not alumno_pertenece_a_clase_actual_profesor (id_profesor, dni):
        flash ("El DNI del alumno no corresponde a la clase del profesor o no existe", "warning")
        return redirect(url_for("profesor.listado_alumnos"))

    datos = conseguir_perfil_alumno(dni)

    if datos == None:
        flash ("ERROR: el DNI ingresado no existe", "warning")
        return redirect(url_for("profesor.index_profesor"))
    promedio_asistencia = datos.promedio_asistencia
    perfil_alumno = datos[0]
        
    return render_template ('/profesor/perfil_alumno.html',
                            alumno=perfil_alumno,
                            promedio=float(promedio_asistencia)
                            )