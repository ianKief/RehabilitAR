from flask import Blueprint, session, abort, flash, redirect, url_for, render_template
from src.web.helpers.decorator import requiere_rol
from src.core.database import db

from src.core.reservas import obtener_reserva, AsistenciaReserva
from src.core.asistencias import registrar_presente_alumno, alumno_tiene_asistencia, buscar_clase_por_token, clase_sucediendo_actualmente_por_id

asistencia_bp = Blueprint('asistencia', __name__, url_prefix="/asistencia")

    # estado_actual = 'exito'
    # estado_actual = 'duplicado'
    # estado_actual = 'no_pertenece'
    # estado_actual = 'suspendido'
@asistencia_bp.route("/qr/<token>")
@requiere_rol(["CLIENTE"])
def registrar_asistencia_qr(token):
    clase = buscar_clase_por_token(token)
    id_cliente = session.get('usuario_id')

    # Comprobación 1: clase existe (no comprometemos datos)
    if clase is None:
        abort (404)
    
    # Comprobación 2: clase está sucediendo ahora (no comprometemos datos)
    if not clase_sucediendo_actualmente_por_id (clase.id):
        abort (404)

    # Comprobación 3: el cliente está en esta clase
    try:
        reserva = obtener_reserva (id_cliente, clase.id)
        if reserva == None:
            return render_template('profesor/resultado_qr.html', estado='no_pertenece')
        if reserva.asiste == AsistenciaReserva.CANCELADA:
            return render_template('profesor/resultado_qr.html', estado='suspendido')
    except:
        return render_template('profesor/resultado_qr.html', estado='no_pertenece')

    # Comprobación 4: el alumno aún no tiene la asistencia de su clase
    estado_asistencia_alumno = alumno_tiene_asistencia (id_alumno=id_cliente)
    if estado_asistencia_alumno == AsistenciaReserva.PRESENTE:
        return render_template('profesor/resultado_qr.html', estado='duplicado')


    registrar_presente_alumno (id_alumno=id_cliente)
    db.session.commit()

    return render_template('profesor/resultado_qr.html', estado='exito')