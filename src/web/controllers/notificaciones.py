from flask import Blueprint, request, current_app, redirect, flash, url_for, session, render_template, jsonify
from src.web.helpers.decorator import requiere_rol

from src.core.notificaciones import core_marcar_como_leido, conseguir_notificacion_por_id, notificacion_es_de_usuario, conseguir_notificaciones_habilitadas, switch_configuracion_notificacion
bp = Blueprint("notificaciones", __name__, url_prefix="/notificaciones")

def devolver_notificaciones_configurables ():
    from src.core.notificaciones.notificaciones import TipoNotificacion
    return [TipoNotificacion.PAGOS, TipoNotificacion.NUEVO_BENEFICIO, TipoNotificacion.NUEVA_CLASE_SUGERIDA, TipoNotificacion.NUEVA_APELACION_A_CLASE, TipoNotificacion.ESTADO_POSTULACION_CLASE, TipoNotificacion.ESTADO_CLASE_APELADA, TipoNotificacion.CLASE_COLAPSADA]

def filtrar_notificaciones_configurables (lista_configuraciones):
    list = []
    configurables = devolver_notificaciones_configurables()
    for configuracion in lista_configuraciones:
        if configuracion.tipo in configurables:
            list.append(configuracion)
    return list

def filtrar_notificaciones_no_configurables (lista_configuraciones):
    list = []
    configurables = devolver_notificaciones_configurables()
    for configuracion in lista_configuraciones:
        if configuracion.tipo not in configurables:
            list.append(configuracion)
    return list

# TODO Poner acá comprobación de USUARIO
@bp.route("/<id_notificacion>/marcar_como_leido", methods=["POST"])
def marcar_como_leido(id_notificacion):
    try:
        id_usuario = session.get("usuario_id")
        if not id_usuario:
            return redirect(url_for("auth.login"))
        core_marcar_como_leido(id_usuario, id_notificacion)
    except ValueError as e:
        flash (str(e), "warning")
        return jsonify({})
    except Exception:
        flash ("Ha ocurrido un error", "warning")
        return jsonify({})
    return jsonify({"status": "success", "message": "Notificación leída"})

@bp.route("/<id_notificacion>/detalle", methods=["GET"])
def detalle(id_notificacion):
    id_usuario = session.get("usuario_id")
    if not id_usuario:
        return redirect(url_for("auth.login"))
    if not notificacion_es_de_usuario (id_usuario, id_notificacion):
        flash ("Notificación no válida")
        return
    try:
        notificacion = conseguir_notificacion_por_id(id_notificacion)
        if not notificacion.leido:
            core_marcar_como_leido(id_usuario, id_notificacion)
    except ValueError as e:
        flash (str(e), "warning")
        return
    return render_template("notificaciones/detalle_notificacion.html", notificacion=notificacion)

@bp.route("/configuracion", methods=["GET"])
def configuracion():
    id_usuario = session.get("usuario_id")
    if not id_usuario:
        return redirect(url_for("auth.login"))
        
    notificaciones_habilitadas = conseguir_notificaciones_habilitadas(id_usuario)
    modificables = filtrar_notificaciones_configurables(notificaciones_habilitadas)
    fijas = filtrar_notificaciones_no_configurables(notificaciones_habilitadas)
    print ("Llegué hasta acá")
    return render_template('notificaciones/config_notificaciones.html', modificables = modificables, fijas = fijas)

@bp.route("/configuracion/switch/<id_config>", methods=["POST"])
def switch_configuracion (id_config):
    try:
        id_usuario = session.get("usuario_id")
        if not id_usuario:
            return redirect(url_for("auth.login"))

        switch_configuracion_notificacion (id_config)
        
    except ValueError as e:
        flash (str(e), "warning")
        return jsonify({})
    except Exception:
        flash ("Ha ocurrido un error", "warning")
        return jsonify({})
    return jsonify({"status": "success", "message": "Configuración cambiada"})