from flask import Blueprint, session, abort, flash, redirect, url_for, render_template
from src.web.helpers.decorator import requiere_rol
from src.core.database import db

from src.core.reservas import obtener_reserva, AsistenciaReserva
from src.core.asistencias import registrar_presente_alumno, alumno_tiene_asistencia, buscar_clase_por_token, clase_sucediendo_actualmente_por_id

asistencia_bp = Blueprint('asistencia', __name__, url_prefix="/asistencia")

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
            flash ("No se tiene una reserva para la clase seleccionada", "warning")
            return redirect(url_for("home"))
        if reserva.asiste == AsistenciaReserva.CANCELADA:
            flash ("La reserva actual se encuentra cancelada. Para más información por favor comuníquese con el administrativo", "warning")
            return redirect(url_for("home"))
    except:
        flash ("No se ha podido verificar que el cliente pertenece a la clase", "warning")
        return redirect(url_for("home"))

    # Comprobación 4: el alumno aún no tiene la asistencia de su clase
    estado_asistencia_alumno = alumno_tiene_asistencia (id_alumno=id_cliente)
    if estado_asistencia_alumno == AsistenciaReserva.PRESENTE:
        flash ("El alumno ya tiene su asistencia marcada", "success")
        return redirect(url_for("home"))

    registrar_presente_alumno (id_alumno=id_cliente)
    db.session.commit()

    flash ("Se ha registrado la asistencia con éxito", "success")
    return redirect(url_for("home"))
    # TODO agregar una página como la gente