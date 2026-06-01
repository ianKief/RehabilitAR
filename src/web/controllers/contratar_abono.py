from datetime import date
from src.web.controllers.pagos import crear_preferencia_mp,calcular_descuento_maximo
from flask import Blueprint, request, current_app, redirect,flash,url_for
from flask import session
from src.core.pagos import estado_abono,obtener_ultimo_abono,calcular_valor_abono

bp = Blueprint("contratar_abono", __name__)

#ruta que procesa la contratación de un nuevo abono
@bp.route("/", methods=["POST"])
def contratar_abono_route():
    
    #obtiene el SDK de Mercado Pago inicializado en Flask
    sdk = current_app.mp_sdk
    
    #obtiene el día fijo elegido por el usuario desde el formulario HTML
    dia_semana_elegido = int(request.form["dia_fijo"])
    
    #obtiene el ID del usuario logueado desde la sesión
    user_id = session.get("usuario_id")
    print("USER_ID EN SESSION:", session.get("usuario_id"))


    descuento = 0

    if request.form.get("descuento"):
        descuento = calcular_descuento_maximo(user_id,dia_semana_elegido)
    
    abono = obtener_ultimo_abono(user_id)

    if abono and estado_abono(abono) == "activo":
        flash("Ya tenés un abono activo", "warning")
        return redirect(url_for("home"))
    
    #crea la preferencia de pago en Mercado Pago
    resultado = calcular_contratacion_abono(dia_semana_elegido, descuento, sdk,user_id)
    print(resultado)
    #redirige al usuario a Mercado Pago
    return redirect(resultado["response"]["init_point"])



#calcula el valor del abono y crea la preferencia de pago
def calcular_contratacion_abono(dia_semana_elegido, descuento, sdk, user_id):
    import os

    URL = ""
    
    # 1. Intentamos obtener la URL pública real consultando directamente a los túneles activos de ngrok
    try:
        from pyngrok import ngrok
        tunnels = ngrok.get_tunnels()
        if tunnels:
            URL = tunnels[0].public_url
    except Exception:
        pass
    
    # 2. Si falla, obtenemos la URL de Ngrok del archivo .env
    if not URL:
        URL = os.environ.get('URL_NGROK', '')
        
    # Si no hay URL de Ngrok, usamos la URL base de la petición actual para evitar rutas relativas
    if not URL:
        URL = request.url_root
        
    URL = URL.rstrip('/')

    #calcula el precio final del abono
    valor = calcular_valor_abono(dia_semana_elegido)

    valor = valor * (1- descuento)

    #datos enviados a Mercado Pago
    preference_data = {
        "items": [{
            "title": "Abono mensual",
            "quantity": 1,
            "unit_price": valor
        }],
        #guarda el usuario asociado al pago
        "external_reference": str(user_id),

        #datos personalizados enviados a Mercado Pago
        #se recuperan luego desde el webhook
        "metadata": {
            "dia_fijo": dia_semana_elegido,
            "descuento_usuario": descuento
        },

        "back_urls": {
            "success": f"{URL}{url_for('pagos.pago_exitoso')}",
            "failure": f"{URL}{url_for('pagos.pago_fallido')}",
            "pending": f"{URL}{url_for('pagos.pago_pendiente')}"
        },
        "notification_url": f"{URL}{url_for('pagos.webhook')}"
    }

    print("URL:", repr(URL))
    print("VALOR:", repr(valor))
    print("PAYLOAD:")
    from pprint import pprint
    pprint(preference_data)
    
    #crea la preferencia de pago utilizando el SDK de Mercado Pago
    return crear_preferencia_mp(sdk, preference_data)