from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select, exists

from src.core.database import db
from src.core.usuarios import Usuario
from src.core.notificaciones.notificaciones import Notificacion, TipoNotificacion, ConfiguracionNotificacion

def obtener_notificaciones_del_usuario (usuario_id):
    query = (db.session.query(Notificacion)
        .filter(Notificacion.id_usuario == usuario_id)
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

def enviar_notificaciones (destinatarios, titulo, contenido, tipo_notificacion=TipoNotificacion.OTRO):
    """Las comprobaciones de funciones hacer en su respectiva función. Envía las notificaciones y mails correspondientes"""
    for destinatario in destinatarios:
        crear_notificacion(destinatario, titulo, contenido, tipo_notificacion)

    # Enviar mails
        # Enviar datos en forma de solicitud :P