from sqlalchemy import select
from src.core.notificaciones.notificaciones import Notificacion

class NotificacionesSeeder:
    def __init__(self, db):
        self.db = db

    def run(self):
        print("🌱 Poblando notificaciones de prueba...")
        try:
            if self.db.session.query(Notificacion).first():
                print("💡 Notificaciones ya existentes, no se realizaron cambios.")
                return

            notificacion = Notificacion (
                titulo = "TITULO",
                contenido = "Este es un mensaje!",
                id_usuario = 2 #cliente
            )
            self.db.session.add(notificacion)
            self.db.session.commit()
            print("✅ Notificaciones de prueba pobladas con éxito.")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error al poblar notificaciones: {e}")