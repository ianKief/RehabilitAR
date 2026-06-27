#importo herramientas
from flask import Blueprint, jsonify, current_app
from flask import request,render_template, redirect,url_for, flash
from src.core.pagos import estado_abono_usuario, procesar_mercado_pago_webhook,calcular_valor_abono
from flask import session
from src.web.helpers.decorator import requiere_rol
from src.core.database import db
from src.core.notificaciones import enviar_notificaciones

from src.core.pagos import PrecioClase, Pago, TipoBeneficio, devolver_pagos_de_reservas_de_usuarios, devolver_abonos_de_usuarios, conseguir_precio_actual, tiene_beneficios, calcular_descuento_maximo


bp = Blueprint("pagos", __name__)


#crea una preferencia de pago utilizando el SDK de Mercado Pago
def crear_preferencia_mp(sdk, preference_data):
    return sdk.preference().create(preference_data)


#pantalla principal de suscripción
@bp.route("/contratar_abono/suscripcion")
@requiere_rol(["CLIENTE"])
def suscripcion():

    id_cliente = session.get("usuario_id")
    precios = {}
    descuentos_por_dia = {}

    for dia in range(5):
        precios[dia] = calcular_valor_abono(dia)
        descuentos_por_dia[dia] = calcular_descuento_maximo(id_cliente,dia)
    
    tiene_descuento = tiene_beneficios(id_cliente,tipo=TipoBeneficio.DESCUENTO)

    estado_actual = estado_abono_usuario(id_cliente)

    return render_template(
        "pagos/suscripcion.html",
        precios=precios,
        descuentos_por_dia=descuentos_por_dia,
        tiene_descuento=tiene_descuento,
        estado_abono=estado_actual
    )

#pantalla mostrada cuando el pago fue exitoso
@bp.route("/contratar_abono/pago_exitoso")
def pago_exitoso():
    return render_template("pagos/pago_exitoso.html")

# pantalla mostrada cuando el pago falló
@bp.route("/contratar_abono/pago_fallido")
def pago_fallido():

    tipo = request.args.get("tipo")
    
    if tipo == "cola":
        datos = {
            "mensaje": "No se pudo completar el pago del abono mensual.",
            "url_reintento": url_for("pagos.suscripcion")
        }

    if tipo == "reserva_fija":

        id_clase = request.args.get("id_clase")

        datos = {
            "mensaje": "No se pudo completar el pago de la reserva.",
            "url_reintento": url_for(
                "reservas.abonar_clase_fija",
                id_clase=id_clase
            )
        }
    
    if tipo == "reserva_individual":
        id_clase = request.args.get("id_clase")

        datos = {
            "mensaje": "No se pudo completar el pago de la clase individual.",
            "url_reintento": url_for(
                "reservas.abonar_individual",
                id_clase=id_clase
            )
        }

    if tipo == "cola":
        id_clase = request.args.get("id_clase")

        datos = {
            "mensaje": "No se pudo completar el pago de la reserva de espera.",
            "url_reintento": url_for(
                "reservas.abonar_cola",
                id_clase=id_clase
            )
        }

    return render_template(
        "pagos/pago_fallido.html",
        **datos
    )
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

    precio_actual = conseguir_precio_actual ()

    return render_template(
        "pagos/precio_clase.html",
        precio=precio_actual
    )


@bp.route("/historial-pagos")
@requiere_rol(["CLIENTE"])
def historial_pagos():

    user_id = session.get("usuario_id")

    abonos = devolver_abonos_de_usuarios(user_id)
    pagos = devolver_pagos_de_reservas_de_usuarios(user_id)

    historial = pagos + abonos

    historial.sort(
        key=lambda pago: pago.fecha_creacion,
        reverse=True
    )

    return render_template(
        "pagos/historial_pagos.html",
        historial=historial
    )