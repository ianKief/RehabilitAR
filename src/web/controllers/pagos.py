#importo herramientas
from flask import Blueprint, jsonify, current_app
from flask import request
from flask import render_template
from flask import redirect
from src.core.pagos import procesar_mercado_pago_webhook,calcular_valor_abono
from flask import session


bp = Blueprint("pagos", __name__)


#crea una preferencia de pago utilizando el SDK de Mercado Pago
def crear_preferencia_mp(sdk, preference_data):
    return sdk.preference().create(preference_data)


#pantalla principal de suscripción
@bp.route("/contratar_abono/suscripcion")
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
    return render_template("contratar_abono/pago_exitoso.html")



#pantalla mostrada cuando el pago falló
@bp.route("/contratar_abono/pago_fallido")
def pago_fallido():
    return render_template("contratar_abono/pago_fallido.html")


#pantalla mostrada cuando el pago queda pendiente
@bp.route("/contratar_abono/pago_pendiente")
def pago_pendiente():
    return render_template("contratar_abono/pago_pendiente.html")

# webhook utilizado por Mercado Pago para notificar pagos
@bp.route("/webhook", methods=["POST"])
def webhook():
    print("Entre al webhook")

    sdk = current_app.mp_sdk
    
    data = request.json

    procesar_mercado_pago_webhook(data,sdk)
    print("termine webhook")
    return "OK", 200