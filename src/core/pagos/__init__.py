from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.pagos.pagos import Pago, DetallePago, PrecioClase, ConceptoPago, EstadoPago,Abono, Beneficio, TipoBeneficio
from src.core.usuarios.usuarios import Usuario, Cliente, EstadoUsuario
from src.core.database import db

from src.core.functions import filtro_cliente_abonado

from datetime import timedelta

from flask import current_app

"contratar abono primera vez"
#R1: la activacion del abono dura un mes, si la fecha contr. es 31 -> dura hasta el ult. dia del sig. mes 
def duracion_abono_mensual(fecha_contratacion:date):
    nueva_fecha=fecha_contratacion+relativedelta(months=1)
    return nueva_fecha


#R2: obtiene 20% de descuento si la cant. dias es 4
#R3: no obtiene descuento si la cant. dias es superior a 4
def calcular_descuento_automatico(cantidad_dias):
    if cantidad_dias == 4:
        return 0.2
    return 0.0

#R4: el valor de la clase es dias * valor clase
def valor_abono_mensual(cantidad_dias,valor_clase):
    return cantidad_dias*valor_clase

def contar_dias_semana(dia_semana,fecha_inicio:date,fecha_fin:date):
    contador=0
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() == dia_semana:
            contador+=1
        fecha_actual+=timedelta(days=1)
    return contador

def calcular_valor_abono(dia_semana_elegido):
    fecha = date.today()

    dias = contar_dias_semana(
        dia_semana_elegido,
        fecha,
        duracion_abono_mensual(fecha)
    )

    valor = valor_abono_mensual(dias,obtener_precio_clase_actual())*(1-calcular_descuento_automatico(dias))

    return valor


def estado_abono_usuario(user_id):

    abono = (
        db.session.query(Abono)
        .join (Pago)
        .filter(Pago.id_cliente == user_id)
        .order_by(Abono.fecha_fin.desc())
        .first()
    )

    return estado_abono(abono)


def estado_abono(abono):

    if not abono:
        return "sin_abono"

    hoy = datetime.today()

    # vencido
    if abono.fecha_fin < hoy:
        return "vencido"

    # opcional futuro (si lo usás más adelante)
    if abono.fecha_fin < hoy - timedelta(days=10):
        return "suspendido"

    return "activo"


"consultas de abono y precio"

def obtener_precio_clase_actual():
    stmt = (
        select(PrecioClase)
        .order_by(PrecioClase.fecha_creacion.desc())
        .limit(1)
    )

    precio = db.session.execute(stmt).scalars().first()

    if not precio:
        return 100  # fallback

    return precio.precio


def obtener_ultimo_abono(user_id):

    stmt = (
        select(Abono)
        .join(Pago)
        .where(Pago.id_cliente == user_id)
        .order_by(Abono.fecha_fin.desc())
    )

    return db.session.execute(stmt).scalars().first()


def registrar_abono(id_pago, dia_fijo):
    fecha_inicio = datetime.today()

    fecha_fin = fecha_inicio + relativedelta(months=1)

    nuevo_abono = Abono(
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
        estado_pago=EstadoPago.COMPLETADO,
        concepto_pago= ConceptoPago.ABONO
    )

    db.session.add(pago)
    db.session.flush()

    detalle_pago = DetallePago(
        id_pago=pago.id,
        cantidad=1,
        precio_unitario=monto,
        subtotal=monto,
    )

    db.session.add(detalle_pago)
    db.session.commit()

    return pago

def consumir_descuentos(id_cliente, pago, limite):

    descuentos = devolver_beneficios_activos(id_cliente,tipo=TipoBeneficio.DESCUENTO   )
    restante = limite
    for beneficio in descuentos:
        if restante <= 0:
            break
        disponible = beneficio.porcentaje_descuento
        if disponible <= restante:
            restante -= disponible
            beneficio.porcentaje_descuento = 0
            beneficio.usado = True
        else:
            beneficio.porcentaje_descuento -= restante
            restante = 0
        beneficio.id_pago = pago.id

def registrar_pago_desde_payment(payment_id,payment):
    monto = payment.get("transaction_amount")
    estado = payment.get("status")

    metadata = payment.get("metadata") or {}
    dia_fijo = metadata.get("dia_fijo")
    print ("El día fijo es:", dia_fijo)
    
    tipo = metadata.get("tipo") 
    print ("TIPO EXISTE????", tipo)

    # si no está aprobado, no hacer nada
    if estado != "approved" :
        print("Pago no aprobado:", estado)
        return
    
    # evitar duplicado
    if pago_ya_procesado(payment_id):
        print("Pago duplicado")
        return
    
    external_ref = payment.get("external_reference")
    if not external_ref:
        return
    user_id = int(external_ref)

    descuento = float(metadata.get("descuento_usuario", 0))
    print ("ESTE DATO DICE SI TIENE DESCUENTO :O", descuento)

    pago = registrar_pago_abono_mensual(payment_id, user_id, monto)

    if descuento>0:
        consumir_descuentos(user_id, pago, descuento)

    registrar_abono (pago.id, dia_fijo)

    db.session.commit()



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



"precio clase"
def obtener_precio_actual():
    return (
        db.session.query(PrecioClase)
        .order_by(PrecioClase.fecha_creacion.desc())
        .first()
    )

def obtener_valor_actual():
    precio = obtener_precio_actual()
    return precio.precio if precio else 0


def actualizar_precio(nuevo_precio):
    precio = PrecioClase(precio=nuevo_precio)
    db.session.add(precio)
    db.session.commit()




def bloquear_morosos_abono():
    """
    Bloquea a los clientes abonados cuyo abono esté vencido.
    Diseñado para ejecutarse el día 11 de cada mes.
    """
    hoy = date.today()
    
    # Control de seguridad: Si no es el día 11, no hacemos nada
    if hoy.day != 11:
        return 0 
        
    # Buscamos a todos los clientes activos que sean abonados
    stmt = (
        select(Cliente)
        .filter(*filtro_cliente_abonado(Cliente.id))
        .filter(Cliente.estado == EstadoUsuario.ACTIVO)
    )
    clientes_abonados = db.session.execute(stmt).scalars().all()
    
    bloqueados = 0
    
    for cliente in clientes_abonados:
        estado_actual = estado_abono_usuario(cliente.id)
        
        # Si su último abono ya venció o no tiene, se lo bloquea
        if estado_actual in ["vencido", "sin_abono"]:
            cliente.estado = EstadoUsuario.BLOQUEADO
            bloqueados += 1
            
    db.session.commit()
    return bloqueados

def devolver_abonos_de_usuarios (id_usuario):
    stmt = (
        select(Pago)
        .where(Pago.concepto_pago == ConceptoPago.ABONO)
        .options(selectinload(Pago.abono))
        .where(Pago.id_cliente == id_usuario)
        .order_by(Pago.fecha_creacion.desc())
    )

    return db.session.execute(stmt).scalars().all()

def devolver_pagos_de_reservas_de_usuarios (id_usuario):
    stmt = (
        select(Pago)
        .where(Pago.concepto_pago == ConceptoPago.RESERVA)
        .options(selectinload(Pago.detalle_pago))
        .where(Pago.id_cliente == id_usuario)
        .order_by(Pago.fecha_creacion.desc())
    )

    return db.session.execute(stmt).scalars().all()

def tiene_beneficios (id_cliente, tipo = TipoBeneficio.CREDITO):
    """Dado el DNI de un cliente, devuelve si tiene créditos o no (Boolean).
    tipo acepta un objeto tipo TipoBeneficio. Entradas posibles: CREDITO o DESCUENTO"""
    query = (db.session.query(Beneficio)
        .join(Cliente, Cliente.id == Beneficio.id_cliente)
        .filter (Cliente.id == id_cliente)
        .filter (Beneficio.tipo == tipo)
        .filter (Beneficio.usado.is_(False))
    )

    return db.session.query(
        query.exists()
    ).scalar()

def devolver_beneficios_activos (id_cliente, tipo=TipoBeneficio.CREDITO):

    query = (db.session.query(Beneficio)
        .join(Cliente, Cliente.id == Beneficio.id_cliente)
        .filter (Cliente.id == id_cliente)
        .filter (Beneficio.usado.is_(False))
        .filter (Beneficio.tipo == tipo)
    )

    return db.session.scalars(query).all()

def registrar_beneficio (id_cliente, descripcion = None, tipo = TipoBeneficio.CREDITO, session=None, porcentaje_descuento=0):
    """Registra un nuevo beneficio para el cliente
    tipo es un objeto TipoBeneficio. Sus entradas posibles son CREDITO o DESCUENTO
    Puede ingresársele un session en caso de contemplar rollback"""
    if (session == None):
        session = db.session

    nuevo_credito = Beneficio (
        id_cliente = id_cliente,
        tipo = tipo,
        descripcion = descripcion,
    )
    session.add(nuevo_credito)
    session.flush()

def conseguir_precio_actual ():
    return (
        db.session.query(PrecioClase)
        .order_by(PrecioClase.fecha_creacion.desc())
        .first()
    )

def calcular_descuento_maximo(id_cliente, dia_semana):
    fecha = date.today()
    dias = contar_dias_semana(dia_semana,fecha,duracion_abono_mensual(fecha))
    descuento_automatico = calcular_descuento_automatico(dias)
    maximo_usuario = 0.30 - descuento_automatico
    if maximo_usuario < 0:
        maximo_usuario = 0
    descuentos = devolver_beneficios_activos(id_cliente,tipo=TipoBeneficio.DESCUENTO)
    total = 0
    for descuento in descuentos:
        total += descuento.porcentaje_descuento
    total = min(total, 0.30)
    return min(total, maximo_usuario)


#cosas que implementare mas adelante



# def abono_esta_activo(abono):
#     if not abono:
#         return False

#     return abono.activo and abono.fecha_fin >= datetime.today()

# def usuario_tiene_abono_activo(user_id):

#     stmt = (
#         select(Abono)
#         .where(Abono.id_cliente == user_id)
#         .order_by(Abono.fecha_fin.desc())
#     )

#     abono = db.session.execute(stmt).scalars().first()

#     if not abono or estado_abono(abono) == "suspendido":
#         return False

#     return estado_abono(abono) == "activo"

# def calcular_monto_renovacion(abono,dia_fijo,descuento_usuario=0.0):
#     valor_clase = obtener_precio_clase_actual()

#     fecha_actual = date.today()

#     fecha_fin = duracion_abono_mensual(
#         fecha_actual
#     )

#     dias = contar_dias_semana(
#         dia_fijo,
#         fecha_actual,
#         fecha_fin
#     )
    
#     descuento_base=calcular_descuento_automatico(dias)

#     descuento_total=calcular_descuento_total(descuento_base,descuento_usuario)

#     valor_total = valor_abono_mensual(dias,valor_clase)*(1-descuento_total)

#     return valor_total

# def validar_descuento_usuario(descuento_usuario):
#     if descuento_usuario < 0:
#         return 0.0
#     if descuento_usuario > 0.30:
#         return 0.30
#     return descuento_usuario


# def calcular_descuento_total(descuento_auto, descuento_usuario):
#     descuento_usuario = validar_descuento_usuario(descuento_usuario)

#     total = descuento_auto + descuento_usuario

#     if total > 0.30:
#         total = 0.30

#     return total



# def renovar_abono(id_cliente,dia_fijo):
    
#     # busca el ultimo abono del usuario
#     abono = db.session.execute(
#         select(Abono)
#         .where(Abono.id_cliente == id_cliente)
#         .order_by(Abono.fecha_fin.desc())
#     ).scalars().first()
    
#     #validar si se puede renovar
#     if not abono or not puede_renovar(abono):
#         return False

#     #extiende la fecha
#     abono.fecha_fin = abono.fecha_fin + relativedelta(months=1)    
    
#     abono.dia_fijo=dia_fijo

#     #Reactiva el abono
#     abono.activo = True

#     #guarda cambios
#     db.session.commit()
#     return True

# def iniciar_renovacion_abono(user_id):
#     abono = obtener_ultimo_abono(user_id)

#     if not abono or not puede_renovar(abono):
#         return None
    

#     monto = calcular_monto_renovacion(abono)

#     return {
#         "user_id": user_id,
#         "abono_id": abono.id,
#         "monto": monto
#     }

# def estado_abono(abono):

#     if not abono:
#         return "sin_abono"

#     hoy = datetime.today()

#     if not abono.activo:
#         return "suspendido"

#     if abono.fecha_fin < hoy - timedelta(days=10):
#         return "suspendido"  

#     if abono.fecha_fin < hoy:
#         return "vencido"

#     return "activo"

# def puede_renovar(abono):

#     if not abono:
#         return False

#     hoy = datetime.today()

#     return hoy <= abono.fecha_fin + timedelta(days=10)