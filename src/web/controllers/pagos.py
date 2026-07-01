#importo herramientas
from flask import Blueprint, current_app
from flask import request,render_template, redirect,url_for, flash
import os
from src.core.pagos import procesar_mercado_pago_webhook, obtener_precio_clase_actual, pago_ya_procesado, registrar_pago_abono_mensual, crear_preferencia_mp
from flask import session
from src.web.helpers.decorator import requiere_rol
from src.core.database import db
from src.core.reservas import obtener_clase_por_id

from src.core.pagos import devolver_pagos_de_reservas_de_usuarios, devolver_abonos_de_usuarios, conseguir_precio_actual, actualizar_precios_clase


bp = Blueprint("pagos", __name__)


def _obtener_url_base() -> str:
    """Helper para obtener la URL base de la aplicación, priorizando Ngrok si está disponible."""
    return os.getenv("URL_NGROK", request.url_root).rstrip('/')

@bp.route("/pagar-abono", methods=["POST"])
@requiere_rol(["CLIENTE"])
def pagar_abono():
    """
    Recibe la confirmación final y crea la preferencia de pago en Mercado Pago.
    """
    sdk = current_app.mp_sdk
    user_id = session.get("usuario_id")
    
    id_clase_origen = request.form.get("id_clase_origen")
    # Recuperamos los datos de la sesión que guardamos en el paso anterior
    reserva_data = session.get('reserva_mensual_post_data', {})
    clases_seleccionadas_ids = reserva_data.get('clases_seleccionadas', [])
    precio_clase_fija = obtener_precio_clase_actual("Fija")
    valor_final = len(clases_seleccionadas_ids) * precio_clase_fija

    if not clases_seleccionadas_ids or valor_final <= 0:
        flash("El monto a pagar no puede ser cero. Por favor, revisá las clases seleccionadas.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    URL_BASE = _obtener_url_base()
    url_exito = f"{URL_BASE}{url_for('pagos.pago_exitoso', tipo='abono')}"

    preference_data = {
        "items": [{"title": "Abono mensual RehabilitAR", "quantity": 1, "unit_price": float(valor_final)}],
        "external_reference": str(user_id),
        "metadata": {
            "tipo": "abono",
            "clases_ids": ",".join(map(str, clases_seleccionadas_ids)) # Enviamos los IDs como string
        },
        "back_urls": {
            "success": url_exito,
            "failure": f"{URL_BASE}{url_for('pagos.pago_fallido', tipo='abono')}",
            "pending": f"{URL_BASE}{url_for('pagos.pago_pendiente', tipo='abono')}"
        },
        "notification_url": url_for('pagos.webhook', _external=True),
        "auto_return": "approved"
    }

    try:
        resultado = crear_preferencia_mp(sdk, preference_data)
        return redirect(resultado["response"]["init_point"])
    except (KeyError, Exception) as e:
        print(f"Error al crear preferencia de pago en pagar_abono: {e}")
        flash("Ocurrió un error inesperado al procesar el pago. Por favor, contactá a soporte.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

# webhook utilizado por Mercado Pago para notificar pagos
@bp.route("/webhook", methods=["POST"])
def webhook():
    print("Entre al webhook")

    sdk = current_app.mp_sdk
    
    data = request.json

    procesar_mercado_pago_webhook(data,sdk)
    print("termine webhook")
    return "OK", 200

#pantalla mostrada cuando el pago fue exitoso
@bp.route("/pago_exitoso")
def pago_exitoso():
    """
    Página de éxito genérica. Si el pago es de un abono,
    procesa el registro de forma sincrónica para asegurar la consistencia.
    """
    tipo = request.args.get("tipo")

    if tipo == "abono":
        sdk = current_app.mp_sdk
        payment_id = request.args.get("payment_id")
        status = request.args.get("status")
        user_id = session.get("usuario_id")

        # Fallback por si se pierde la sesión
        if not user_id:
            external_reference = request.args.get("external_reference")
            user_id = int(external_reference) if external_reference and external_reference.isdigit() else None

        if status == "approved" and payment_id and user_id:
            if not pago_ya_procesado(payment_id):
                try:
                    payment_info = sdk.payment().get(payment_id)
                    monto = payment_info["response"]["transaction_amount"]
                    metadata = payment_info["response"]["metadata"]
                    clases_ids_str = metadata.get("clases_ids", "")
                    clases_seleccionadas_ids = [int(cid) for cid in clases_ids_str.split(',') if cid]

                    pago_abono = registrar_pago_abono_mensual(payment_id, user_id, monto)
                    from src.core.reservas import procesar_reservas_mensuales_automatica
                    clases_a_reservar_obj = [obtener_clase_por_id(cid) for cid in clases_seleccionadas_ids]
                    procesar_reservas_mensuales_automatica(user_id, clases_a_reservar_obj, id_pago_abono=pago_abono.id)
                    flash("¡Pago exitoso! Tu abono está activo y tus clases fueron reservadas.", "success")
                except Exception as e:
                    print(f"Error al registrar el abono en pago_exitoso: {e}")
                    flash("Tu pago fue exitoso, pero hubo un problema al activar tu abono. Por favor, contactá a soporte.", "danger")
        return redirect(url_for('reservas.mis_clases'))

    return render_template("pagos/pago_exitoso.html")

# pantalla mostrada cuando el pago falló
@bp.route("/pago_fallido")
def pago_fallido():

    tipo = request.args.get("tipo")
    id_clase = request.args.get("id_clase")

    # URL de reintento por defecto
    url_reintento = url_for("reservas.calendario_cliente")
    mensaje = "No se pudo completar el pago."

    if tipo == "abono":
        mensaje = "No se pudo completar el pago del abono mensual."
        # Para el abono, el reintento es volver al calendario.
    elif tipo == "reserva_fija":
        mensaje = "No se pudo completar el pago de la reserva."
        url_reintento = url_for("reservas.abonar_clase_fija", id_clase=id_clase)
    elif tipo == "reserva_individual":
        mensaje = "No se pudo completar el pago de la clase individual."
        url_reintento = url_for("reservas.abonar_individual", id_clase=id_clase)
    elif tipo == "cola":
        mensaje = "No se pudo completar el pago para la lista de espera."
        url_reintento = url_for("reservas.abonar_cola", id_clase=id_clase)

    datos = {
        "mensaje": mensaje,
        "url_reintento": url_reintento
    }

    return render_template(
        "pagos/pago_fallido.html",
        **datos
    )

#pantalla mostrada cuando el pago queda pendiente
@bp.route("/pago_pendiente")
def pago_pendiente():
    return render_template("pagos/pago_pendiente.html")

@bp.route("/admin/precio-clase", methods=["GET", "POST"])
@requiere_rol(["ADMINISTRADOR"])
def precio_clase():

    if request.method == "POST":
        precio_individual = request.form.get("precio_individual")
        precio_fija = request.form.get("precio_fija")

        try:
            # Usamos el core para actualizar los precios
            actualizar_precios_clase(
                precio_individual=precio_individual,
                precio_fija=precio_fija
            )
            flash("Precios actualizados correctamente", "success")
        except ValueError as e:
            flash(str(e), "danger")
        
        return redirect(url_for("pagos.precio_clase"))

    # Conseguimos ambos precios para mostrarlos en el formulario
    precio_individual = conseguir_precio_actual("Individual")
    precio_fija = conseguir_precio_actual("Fija")

    return render_template(
        "pagos/precio_clase.html",
        precio_individual=precio_individual,
        precio_fija=precio_fija
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