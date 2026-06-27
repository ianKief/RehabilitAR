from sqlalchemy import select
from src.core.notificaciones.notificaciones import Notificacion

class NotificacionesSeeder:
    def __init__(self, db):
        self.db = db

    def run(self):
        print("Insertando notificaciones...")

        notificacion = Notificacion (
            titulo = "TITULO",
            contenido = "Este es un mensaje!",
            id_usuario = 2 #cliente
        )
        self.db.session.add(notificacion)
        self.db.session.commit()