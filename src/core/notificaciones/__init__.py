from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select

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