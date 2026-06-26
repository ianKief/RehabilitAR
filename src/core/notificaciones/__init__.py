from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select, exists

from src.core.database import db
from src.core.notificaciones.notificaciones import Notificacion, TipoNotificacion, ConfiguracionNotificacion

def obtener_notificaciones_del_usuario (usuario_id):
    query = (db.session.query(Notificacion)
        .filter(Notificacion.id_usuario == usuario_id)
        .order_by(Notificacion.fecha_creacion.desc())
    )
    return db.session.scalars(query).all()

def contar_notificaciones_no_leidas (usuario_id):
    query = (select(func.count(Notificacion.id))
        .filter(Notificacion.id_usuario == usuario_id)
        .filter(Notificacion.leido == False)
    )
    return db.session.execute(query).scalar()

def notificacion_es_de_usuario (id_usuario, id_notificacion):
    query =(select(exists(Notificacion.id))
        .filter(Notificacion.id_usuario == id_usuario)
        .filter (Notificacion.id == id_notificacion)
    )
    return db.session.execute(query).scalar()

def conseguir_notificacion_por_id (id):
    return db.session.scalar(select(Notificacion).filter(Notificacion.id == id))

def core_marcar_como_leido (id_usuario, id_notificacion):
    if not notificacion_es_de_usuario (id_usuario, id_notificacion):
        raise ValueError("La notificación no es del usuario!")

    notificacion = conseguir_notificacion_por_id (id_notificacion)
    notificacion.leido = True
    db.session.commit()

def crear_notificacion (destinatario, titulo, contenido, tipo_notificacion):
    """Solo lo usa enviar_notificaciones"""
    print ("Llegué a crear_notificacion")
    configuracion = db.session.query(ConfiguracionNotificacion).filter(ConfiguracionNotificacion.tipo == tipo_notificacion).filter(ConfiguracionNotificacion.id_usuario == destinatario.id).scalar()
    if configuracion.habilitado and configuracion.activado:
        nueva_notificacion = Notificacion (
            tipo = tipo_notificacion,
            titulo = titulo,
            contenido = contenido,
            usuario = destinatario
        )
        db.session.add(nueva_notificacion)
        db.session.flush()

def conseguir_mails (iterable):
    list = []
    for user in iterable:
        list.append(user.email)
    return list

def enviar_notificaciones (destinatarios, titulo, contenido, tipo_notificacion=TipoNotificacion.OTRO):
    """Las comprobaciones de funciones hacer en su respectiva función. Envía las notificaciones y mails correspondientes"""
    from src.core.mail import enviar_correo
    try:
        if isinstance(destinatarios, list):
            iterable = destinatarios
        else:
            iterable = [destinatarios]

        for destinatario in iterable:
            print ("Así se ve un destinatario:", destinatario)
            crear_notificacion(destinatario, titulo, contenido, tipo_notificacion)

        db.session.commit()
    except Exception as e:
        print ("Error en las notificaciones:", str(e))
    
    try:
        enviar_correo(subject= f"RehabilitAR - {titulo}", recipients=conseguir_mails(iterable), body=contenido)
    except Exception as e:
        print ("Error en el envío de mail:", str(e))

def conseguir_notificaciones_habilitadas (id_usuario):
    query = (db.session.query(ConfiguracionNotificacion)
        .filter(ConfiguracionNotificacion.id_usuario == id_usuario)
        .filter (ConfiguracionNotificacion.habilitado == True)
        .order_by(ConfiguracionNotificacion.tipo.asc())
    )
    return db.session.scalars(query).all()

def conseguir_configuracion_notificacion_por_id (id_config):
    return db.session.scalar(select(ConfiguracionNotificacion).filter(ConfiguracionNotificacion.id == id_config))

def switch_configuracion_notificacion (id_config):
    config = conseguir_configuracion_notificacion_por_id (id_config)
    if config.habilitado:
        if config.activado:
            config.activado = False
        else:
            config.activado = True
        db.session.commit()
    else:
        raise ValueError("La configuración no está habilitada")
    db.session.commit()