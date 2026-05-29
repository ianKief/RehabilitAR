from datetime import date
from src.web.controllers.pagos import crear_preferencia_mp
from flask import Blueprint, request, current_app, redirect
from flask import session
from src.core.pagos import estado_abono,obtener_ultimo_abono,calcular_valor_abono

bp = Blueprint("contratar_abono", __name__)

#ruta que procesa la contratación de un nuevo abono
@bp.route("/contratar_abono", methods=["POST"])
def contratar_abono_route():
    
    #obtiene el SDK de Mercado Pago inicializado en Flask
    sdk = current_app.mp_sdk
    
    #obtiene el día fijo elegido por el usuario desde el formulario HTML
    dia_semana_elegido = int(request.form["dia_fijo"])
    
    #obtiene el ID del usuario logueado desde la sesión
    user_id = session.get("usuario_id")
    
    print("USER_ID EN SESSION:", session.get("usuario_id"))

    abono = obtener_ultimo_abono(user_id)

    if abono and estado_abono(abono) == "activo":
        return "Ya tenes un abono activo"
    
    #crea la preferencia de pago en Mercado Pago
    resultado = calcular_contratacion_abono(dia_semana_elegido, sdk,user_id)
    print(resultado)
    #redirige al usuario a Mercado Pago
    return redirect(resultado["response"]["init_point"])



#calcula el valor del abono y crea la preferencia de pago
def calcular_contratacion_abono(dia_semana_elegido, sdk, user_id):
    
    #calcula el precio final del abono
    valor = calcular_valor_abono(dia_semana_elegido)

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
            "dia_fijo": dia_semana_elegido
        },

        "back_urls": {
            "success": "https://boss-daybed-chuck.ngrok-free.dev/contratar_abono/pago_exitoso",
            "failure": "https://boss-daybed-chuck.ngrok-free.dev/contratar_abono/pago_fallido",
            "pending": "https://boss-daybed-chuck.ngrok-free.dev/contratar_abono/pago_pendiente"
        },
        "notification_url": "https://boss-daybed-chuck.ngrok-free.dev/webhook"
    }
    
    #crea la preferencia de pago utilizando el SDK de Mercado Pago
    return crear_preferencia_mp(sdk, preference_data)