from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select, exists

from src.core.database import db
from src.core.notificaciones.notificaciones import Notificacion

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