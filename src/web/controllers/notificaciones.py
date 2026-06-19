from flask import Blueprint, request, current_app, redirect, flash, url_for, session, render_template

bp = Blueprint("notificaciones", __name__)

#ruta que procesa la contratación de un nuevo abono
@bp.route("/listar_notificaciones", methods=["POST"])
# Poner acá comprobación de USUARIO
def listar_notificaciones():
    # mis_notificaciones = Usuario.obtener_notificaciones() 
    # cantidad_no_leidas = Usuario.obtener_conteo_no_leidas()

    return render_template(
        'tu_plantilla.html'
        # notificaciones=mis_notificaciones,  # <-- Lista de diccionarios u objetos
        # unread_count=cantidad_no_leidas     # <-- Número entero
    )