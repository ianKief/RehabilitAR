from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy import select
from sqlalchemy.orm import aliased

from src.core.clases import devolver_clase_segun_su_id, Clase
from src.core.pagos.pagos import Beneficio, TipoBeneficio, Pago, DetallePago, DetallePagoReserva, PrecioClase, ConceptoPago, EstadoPago,Abono
from src.core.usuarios import es_abonado, Usuario
from src.core.database import db
from src.core.contratar_abono import contar_dias_semana,calcular_descuento_automatico
from src.core.renovar_abono import renovar_abono

from datetime import timedelta

from flask import current_app

def obtener_info_descuento(abono):
    
    usuario = db.session.get(Usuario, abono.id_cliente)

    dias = contar_dias_semana(
        abono.dia_fijo,
        abono.fecha_inicio,
        abono.fecha_fin
    )

    descuento_auto = calcular_descuento_automatico(dias)

    maximo_por_regla = 0.30 - descuento_auto

    if maximo_por_regla < 0:
        maximo_por_regla = 0.0

    descuento_disponible_usuario = usuario.descuento_acumulado

    maximo_usuario = min(
        descuento_disponible_usuario,
        maximo_por_regla
    )

    return {
        "tiene_descuento": maximo_usuario > 0,
        "max_usuario": maximo_usuario
    }

"consultas de abono y precio"

def obtener_precio_clase_actual():
    stmt = (
        select(PrecioClase)
        .where(
            PrecioClase.fecha_hasta == None
        )
        .order_by(PrecioClase.fecha_creacion.desc())
    )

    precio = db.session.execute(stmt).scalars().first()

    #momentaneo->crear funcion admin para agregar precio a la clase.
    if not precio:
        return 100

    return precio.precio


def obtener_ultimo_abono(user_id):
    stmt = (
        select(Abono)
        .where(Abono.id_cliente == user_id)
        .order_by(Abono.fecha_fin.desc())
    )

    return db.session.execute(stmt).scalars().first()




def registrar_abono(id_cliente, id_pago, dia_fijo):
    fecha_inicio = datetime.today()

    fecha_fin = fecha_inicio + relativedelta(months=1)

    nuevo_abono = Abono(
        id_cliente=id_cliente,
        id_pago=id_pago,
        dia_fijo=dia_fijo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )

    db.session.add(nuevo_abono)
    db.session.commit()

    return nuevo_abono

"Pagos"

def pago_ya_procesado(payment_id):
    stmt = select(Pago).where(Pago.payment_id == str(payment_id))
    pago = db.session.execute(stmt).scalar_one_or_none()
    return pago is not None

def registrar_pago_abono_mensual(payment_id,id_cliente,monto):
    
    pago = Pago(
        payment_id=str(payment_id),
        id_cliente = id_cliente,
        monto_total=monto,
        estado_pago=EstadoPago.COMPLETADO
    )

    db.session.add(pago)
    db.session.flush()

    detalle_pago = DetallePago(
        id_pago=pago.id,
        cantidad=1,
        precio_unitario=monto,
        subtotal=monto,
        concepto_pago=ConceptoPago.RESERVA_MENSUAL
    )

    db.session.add(detalle_pago)
    db.session.commit()

    return pago

def registrar_pago_desde_payment(payment_id,payment):
    monto = payment.get("transaction_amount")
    estado = payment.get("status")

    metadata = payment.get("metadata") or {}
    dia_fijo = metadata.get("dia_fijo")
    
    tipo = metadata.get("tipo") 

    descuento_usuario = float(metadata.get("descuento_usuario", 0.0))
    
    # si no está aprobado, no hacer nada
    if estado != "approved" :
        print("Pago no aprobado:", estado)
        return
    
    # evitar duplicados
    if pago_ya_procesado(payment_id):
        print("Pago duplicado")
        return
    
    external_ref = payment.get("external_reference")
    if not external_ref:
        return
    user_id = int(external_ref)

    usuario = db.session.get(Usuario, user_id)

    usuario.descuento_acumulado -= descuento_usuario

    if usuario.descuento_acumulado < 0:
        usuario.descuento_acumulado = 0
    
    pago=registrar_pago_abono_mensual(payment_id,user_id,monto)


    if tipo == "renovacion":
        renovar_abono(user_id,dia_fijo)
        return
    
    registrar_abono(user_id,pago.id,dia_fijo)



"Webhook"
def procesar_mercado_pago_webhook(data,sdk):

    # valida que venga el ID correctamente
    if not data or "data" not in data or "id" not in data["data"]:
        return
    
    # obtiene el ID del pago enviado por Mercado Pago
    payment_id = data["data"]["id"]

    # consulta pago real en Mercado Pago
    payment_info = sdk.payment().get(payment_id)

    if not payment_info or "response" not in payment_info:
        return

    #obtiene la respuesta real del pago
    payment = payment_info["response"]
    
    # guardar en BD
    registrar_pago_desde_payment(payment_id, payment)

