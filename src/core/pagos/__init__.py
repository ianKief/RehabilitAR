from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.pagos.pagos import Pago, DetallePago, PrecioClase, ConceptoPago, EstadoPago,Abono, Beneficio, TipoBeneficio
from src.core.usuarios.usuarios import Cliente, EstadoUsuario
from src.core.usuarios import informar_alta_demanda, obtener_usuario_por_id_core
from src.core.database import db
from src.core.reservas import crear_reserva, crear_espera_en_cola
from src.core.clases import comprobar_alta_demanda, Clase, obtener_clase_por_id
from src.core.functions import filtro_cliente_abonado
from src.core.notificaciones import enviar_notificaciones, TipoNotificacion

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
    
    #opcional futuro (si lo usás más adelante)
    if abono.fecha_fin < hoy - timedelta(days=10):
        return "suspendido"

    # vencido
    if abono.fecha_fin < hoy:
        return "vencido"

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

# Este nombre es horrible. No expresa su intención
def registrar_pago_abono_mensual(payment_id, id_cliente, monto):
    
    pago = Pago(
        payment_id=str(payment_id),
        id_cliente = id_cliente,
        monto_total=monto,
        estado_pago=EstadoPago.COMPLETADO,
        concepto_pago= ConceptoPago.ABONO
    )

    db.session.add(pago)
    db.session.commit()

    return pago

def consumir_descuentos(id_cliente, pago, limite):

    descuentos = devolver_beneficios_activos(id_cliente,tipo=TipoBeneficio.DESCUENTO)
    restante = limite
    for beneficio in descuentos:
        if restante <= 0:
            break
        disponible = beneficio.porcentaje_descuento

        # el beneficio original se consume
        beneficio.usado = True
        beneficio.id_pago = pago.id

        # se consume completo
        if disponible <= restante:
            restante -= disponible

        # se consume parcialmente
        else:
            sobrante = disponible - restante
            nuevo_beneficio = Beneficio(
                id_cliente=id_cliente,
                tipo=TipoBeneficio.DESCUENTO,
                descripcion="Descuento restante",
                porcentaje_descuento=sobrante,
                usado=False
            )
            db.session.add(nuevo_beneficio)
            restante = 0

def registrar_pago_desde_payment(payment_id, payment):
    monto = payment.get("transaction_amount")
    estado = payment.get("status")

    metadata = payment.get("metadata") or {}
    dia_fijo = metadata.get("dia_fijo")
    
    tipo = metadata.get("tipo") 

    # si no está aprobado, no hacer nada
    if estado != "approved" :
        print("Pago no aprobado:", estado)
        return
    
    if tipo == "reserva_fija":

        external_ref = payment.get("external_reference")

        if not external_ref:
            return

        usuario_id, id_clase = external_ref.split(":")

        usuario_id = int(usuario_id)
        id_clase = int(id_clase)

        # evitar duplicados
        if pago_ya_procesado(payment_id):
            return

        monto = payment.get("transaction_amount")

        pago = Pago(
            payment_id=str(payment_id),
            id_cliente=usuario_id,
            monto_total=monto,
            estado_pago=EstadoPago.COMPLETADO,
            concepto_pago=ConceptoPago.RESERVA
        )

        db.session.add(pago)

        crear_reserva(usuario_id, id_clase)

        db.session.commit()

        clase = obtener_clase_por_id(id_clase)

        contenido_mensaje = f"Se ha confirmado su nueva reserva para la clase fija {clase.nombre}. Puedes ver más información del pago en la sección de pagos y la reserva ya se encuentra activa."
    
    if tipo == "reserva_individual":
        external_ref = payment.get("external_reference")
        if not external_ref:
            return

        usuario_id, id_clase, porcentaje = external_ref.split(":")

        usuario_id = int(usuario_id)
        id_clase = int(id_clase)
        porcentaje = int(porcentaje)

        # evitar duplicados
        if pago_ya_procesado(payment_id):
            return

        monto = payment.get("transaction_amount")
        precio_total = obtener_precio_clase_actual()
        porcentaje = (monto / precio_total) * 100
        print ("Monto:", monto, "Precio total:", precio_total, "Porcentaje:", porcentaje)
        estado_final = (
            EstadoPago.COMPLETADO
            if porcentaje >= 100
            else EstadoPago.PENDIENTE
        )
        
        # 1. crear pago
        pago = Pago(
            payment_id=str(payment_id),
            id_cliente=usuario_id,
            monto_total=monto,
            estado_pago=estado_final,
            concepto_pago=ConceptoPago.RESERVA
        )

        db.session.add(pago)

        # 3. crear reserva REAL
        reserva = crear_reserva(usuario_id, id_clase)

        db.session.flush()

        # 2. detalle
        detalle = DetallePago(
            id_pago=pago.id,
            cantidad=1,
            precio_unitario=monto,
            subtotal=monto,
            reserva = reserva
        )
        db.session.add(detalle)

        db.session.commit()
    
        clase = obtener_clase_por_id(id_clase)

        contenido_mensaje = f"Se ha confirmado su nueva reserva para la clase individual {clase.nombre}. Puedes ver más información del pago en la sección de pagos y la reserva ya se encuentra activa."

    if tipo == "cola":
        external_ref = payment.get("external_reference")
        if not external_ref:
            return
        usuario_id, id_clase = external_ref.split(":")

        usuario_id = int(usuario_id)
        id_clase = int(id_clase)

        # evitar duplicados
        if pago_ya_procesado(payment_id):
            return

        monto = payment.get("transaction_amount")
        pago = Pago(
            payment_id=str(payment_id),
            id_cliente=usuario_id,
            monto_total=monto,
            estado_pago=EstadoPago.COMPLETADO,
            concepto_pago=ConceptoPago.RESERVA # Agregar otro concepto de pago para las colas
        )
        db.session.add(pago)

        # TODO Poner conexión de pago a cola aquí
    
        crear_espera_en_cola (usuario_id, id_clase)
        db.session.commit()

        clase = db.session.query(Clase).filter(Clase.id == id_clase).first()
        if comprobar_alta_demanda (clase):
            informar_alta_demanda (clase)
        
        clase = obtener_clase_por_id(id_clase)

        contenido_mensaje = f"Se ha confirmado su nuevo espacio en la cola para la clase {clase.nombre}. Puedes ver más información del pago en la sección de pagos y el lugar ya se encuentra activo. En caso de vencer dicho espacio, comuníquese con la administración."

    if tipo == "abono":

        if pago_ya_procesado(payment_id):
            print("Pago duplicado")
            return
        
        external_ref = payment.get("external_reference")
        if not external_ref:
            return
        usuario_id = int(external_ref)

        descuento = float(metadata.get("descuento_usuario", 0))

        pago = registrar_pago_abono_mensual(payment_id, usuario_id, monto)

        if descuento > 0:
            consumir_descuentos(usuario_id, pago, descuento)

        registrar_abono (pago.id, dia_fijo)

        contenido_mensaje = "Se ha confirmado su pago del abono. Este pago le permitirá seleccionar una clase fija y reservar todo el mes, además de acceder a múltiples beneficios. Para más información del pago visite la sección pagos."

    enviar_notificaciones(obtener_usuario_por_id_core(usuario_id), "¡Pago realizado exitosamente!", contenido_mensaje, TipoNotificacion.PAGOS)
    db.session.commit()

def registrar_pago_con_credito (cliente, clase, precio):

    pago = Pago (
        id_cliente = cliente.id,
        payment_id = f"Crédito {cliente.id} - {clase.id} usado",
        monto_total = 0,
        estado_pago = EstadoPago.PENDIENTE,
        concepto_pago = ConceptoPago.RESERVA,
    )
    db.session.add(pago)
    db.session.flush()

    try:
        devolver_credito_y_marcar_como_usado (cliente.id, pago.id, db.session)
    except:
        raise ValueError("El cliente no tiene un crédito habilitado")
        db.session.rollback()
    
    try:
        reserva = crear_reserva(cliente.id, clase.id)
    except:
        raise ValueError("Ha habido un problema al crear la reserva")
        db.session.rollback()
    
    db.session.flush()

    detalle = DetallePago(
        id_pago=pago.id,
        cantidad=1,
        precio_unitario=precio,
        subtotal=0,
        reserva = reserva
    )
    db.session.add(detalle)

    pago.estado_pago = EstadoPago.COMPLETADO
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
    from core.usuarios.usuarios import Cliente, EstadoUsuario
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


def notificar_ultimo_dia_de_pago():
    """
    Notifica a los clientes abonados que su abono esta proximo a vencer. 
    Diseñado para ejecutarse el dia 10 de cada mes.
    """

    hoy = date.today()

    if hoy.day != 10:
        return 0
    
    from src.web import mail
    from flask_mail import Message

    stmt = (
        select(Cliente)
        .filter(Cliente.es_abonado == True)
        .filter(Cliente.estado == EstadoUsuario.ACTIVO)
    )
    clientes_abonados = db.session.execute(stmt).scalars().all()

    correos_enviados = 0

    for cliente in clientes_abonados:
        estado_actual = estado_abono_usuario(cliente.id)

        if estado_actual == "vencido":
            msg = Message(
                subject="RehabilitAR - Tu abono vence hoy",
                recipients=[cliente.email]
            )
            msg.body = f"""Hola {cliente.nombre},

                    Te recordamos que tu abono mensual vence hoy. 
                    
                    Si el pago no se registra para el día de mañana, tu cuenta será bloqueada automáticamente por el sistema.

                    Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos.

                    Si ya realizaste el pago, por favor desestimá este mensaje.

                    ¡Gracias por ser parte de RehabilitAR!"""
            
            try:
                mail.send(msg)
                correos_enviados += 1
            except Exception as e:
                print(f"Error al enviar correo a {cliente.email}: {e}")
    
    return correos_enviados


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

def registrar_beneficio (id_cliente, descripcion = None, tipo = TipoBeneficio.CREDITO, porcentaje_descuento=0):
    """Registra un nuevo beneficio para el cliente
    tipo es un objeto TipoBeneficio. Sus entradas posibles son CREDITO o DESCUENTO
    Puede ingresársele un session en caso de contemplar rollback"""

    if tipo == TipoBeneficio.CREDITO:
        nuevo_credito = Beneficio (
            id_cliente = id_cliente,
            tipo = tipo,
            descripcion = descripcion,
        )
        texto_adicional = f"Los créditos pueden usarse para reservar una futura clase individual sin costo alguno."
    else:
        nuevo_credito = Beneficio (
            id_cliente = id_cliente,
            tipo = tipo,
            descripcion = descripcion,
            porcentaje_descuento = porcentaje_descuento
        )
        texto_adicional = f"Los descuentos pueden usarse para futuros pagos de abono. El descuento actual es del {porcentaje_descuento * 100}%"

    enviar_notificaciones(obtener_usuario_por_id_core(id_cliente), f"¡Nuevo beneficio activo!", "Se ha habilitado un nuevo {tipo.value}. {texto_adicional}", TipoNotificacion.NUEVO_BENEFICIO)
    db.session.add(nuevo_credito)
    db.session.flush()

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

def devolver_credito_y_marcar_como_usado (id_cliente, id_pago):
    credito = db.session.query(Beneficio).filter(Beneficio.tipo == TipoBeneficio.CREDITO).filter(Beneficio.id_cliente == id_cliente).filter(Beneficio.usado == False).first()
    
    if credito == None:
        raise ValueError()
    
    credito.usado = True
    credito.id_pago = id_pago

    return credito