#importo herramientas
from flask import Blueprint, jsonify, current_app
from flask import request,render_template, redirect,url_for, flash
from src.core.pagos import procesar_mercado_pago_webhook,calcular_valor_abono
from flask import session
from src.web.helpers.decorator import requiere_rol
from src.core.database import db

from src.core.pagos import PrecioClase, Pago, devolver_pagos_de_reservas_de_usuarios, devolver_abonos_de_usuarios


bp = Blueprint("pagos", __name__)


#crea una preferencia de pago utilizando el SDK de Mercado Pago
def crear_preferencia_mp(sdk, preference_data):
    return sdk.preference().create(preference_data)


#pantalla principal de suscripción
@bp.route("/contratar_abono/suscripcion")
@requiere_rol(["CLIENTE"])
def suscripcion():

    precios = {}

    for dia in range(5):

        precios[dia] = calcular_valor_abono(dia)

    return render_template(
         "pagos/suscripcion.html",
        precios=precios
    )

#pantalla mostrada cuando el pago fue exitoso
@bp.route("/contratar_abono/pago_exitoso")
def pago_exitoso():
    return render_template("pagos/pago_exitoso.html")


#pantalla mostrada cuando el pago falló
@bp.route("/contratar_abono/pago_fallido")
def pago_fallido():
    return render_template("pagos/pago_fallido.html")

#pantalla mostrada cuando el pago queda pendiente
@bp.route("/contratar_abono/pago_pendiente")
def pago_pendiente():
    return render_template("pagos/pago_pendiente.html")

# webhook utilizado por Mercado Pago para notificar pagos
@bp.route("/webhook", methods=["POST"])
def webhook():
    print("Entre al webhook")

    sdk = current_app.mp_sdk
    
    data = request.json

    procesar_mercado_pago_webhook(data,sdk)
    print("termine webhook")
    return "OK", 200

@bp.route("/admin/precio-clase", methods=["GET", "POST"])
@requiere_rol(["ADMINISTRADOR"])
def precio_clase():

    if request.method == "POST":
        nuevo_precio = request.form.get("precio")

        if not nuevo_precio:
            flash("Debes ingresar un precio", "danger")
            return redirect(url_for("pagos.precio_clase"))

        precio = PrecioClase(precio=int(nuevo_precio))
        db.session.add(precio)
        db.session.commit()

        flash("Precio actualizado correctamente", "success")
        return redirect(url_for("pagos.precio_clase"))

    # GET -> traer último precio
    precio_actual = (
        db.session.query(PrecioClase)
        .order_by(PrecioClase.fecha_creacion.desc())
        .first()
    )

    return render_template(
        "pagos/precio_clase.html",
        precio=precio_actual
    )


@bp.route("/historial-pagos")
@requiere_rol(["CLIENTE"])
def historial_pagos():

    user_id = session.get("usuario_id")

    renderizar_lista = False
    abonos = devolver_abonos_de_usuarios (user_id)
    pagos = devolver_pagos_de_reservas_de_usuarios (user_id)

    return render_template(
        "pagos/historial_pagos.html",
        pagos = pagos, abonos = abonos
    )