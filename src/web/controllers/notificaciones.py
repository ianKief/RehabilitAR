from flask import Blueprint, request, current_app, redirect, flash, url_for, session, render_template, jsonify
from src.web.helpers.decorator import requiere_rol

from src.core.notificaciones import core_marcar_como_leido
bp = Blueprint("notificaciones", __name__, url_prefix="/notificaciones")

# Poner acá comprobación de USUARIO
@bp.route("/<id_notificacion>/marcar_como_leido", methods=["POST"])
def marcar_como_leido(id_notificacion):
    id_usuario = session.get("usuario_id")
    print ("Pasé por acá")
    try:
        core_marcar_como_leido(id_usuario, id_notificacion)
    except ValueError as e:
        flash (str(e), "warning")
        return jsonify({})
    return jsonify({"status": "success", "message": "Notificación leída"})

