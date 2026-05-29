from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy import select
from sqlalchemy.orm import aliased

from datetime import timedelta
from pagos import obtener_precio_clase_actual



def abono_esta_activo(abono):
    if not abono:
        return False

    return abono.activo and abono.fecha_fin >= datetime.today()

def usuario_tiene_abono_activo(user_id):

    stmt = (
        select(Abono)
        .where(Abono.id_cliente == user_id)
        .order_by(Abono.fecha_fin.desc())
    )

    abono = db.session.execute(stmt).scalars().first()

    if not abono or estado_abono(abono) == "suspendido":
        return False

    return estado_abono(abono) == "activo"

def calcular_monto_renovacion(abono,dia_fijo,descuento_usuario=0.0):
    valor_clase = obtener_precio_clase_actual()

    fecha_actual = date.today()

    fecha_fin = duracion_abono_mensual(
        fecha_actual
    )

    dias = contar_dias_semana(
        dia_fijo,
        fecha_actual,
        fecha_fin
    )
    
    descuento_base=calcular_descuento_automatico(dias)

    descuento_total=calcular_descuento_total(descuento_base,descuento_usuario)

    valor_total = valor_abono_mensual(dias,valor_clase)*(1-descuento_total)

    return valor_total

def validar_descuento_usuario(descuento_usuario):
    if descuento_usuario < 0:
        return 0.0
    if descuento_usuario > 0.30:
        return 0.30
    return descuento_usuario


def calcular_descuento_total(descuento_auto, descuento_usuario):
    descuento_usuario = validar_descuento_usuario(descuento_usuario)

    total = descuento_auto + descuento_usuario

    if total > 0.30:
        total = 0.30

    return total



def renovar_abono(id_cliente,dia_fijo):
    
    # busca el ultimo abono del usuario
    abono = db.session.execute(
        select(Abono)
        .where(Abono.id_cliente == id_cliente)
        .order_by(Abono.fecha_fin.desc())
    ).scalars().first()
    
    #validar si se puede renovar
    if not abono or not puede_renovar(abono):
        return False

    #extiende la fecha
    abono.fecha_fin = abono.fecha_fin + relativedelta(months=1)    
    
    abono.dia_fijo=dia_fijo

    #Reactiva el abono
    abono.activo = True

    #guarda cambios
    db.session.commit()
    return True

def iniciar_renovacion_abono(user_id):
    abono = obtener_ultimo_abono(user_id)

    if not abono or not puede_renovar(abono):
        return None
    

    monto = calcular_monto_renovacion(abono)

    return {
        "user_id": user_id,
        "abono_id": abono.id,
        "monto": monto
    }

def estado_abono(abono):

    if not abono:
        return "sin_abono"

    hoy = datetime.today()

    if not abono.activo:
        return "suspendido"

    if abono.fecha_fin < hoy - timedelta(days=10):
        return "suspendido"  

    if abono.fecha_fin < hoy:
        return "vencido"

    return "activo"

def puede_renovar(abono):

    if not abono:
        return False

    hoy = datetime.today()

    return hoy <= abono.fecha_fin + timedelta(days=10)