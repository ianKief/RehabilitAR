from sqlalchemy import select
from src.core.usuarios.usuarios import Especialidad, TipoEspecialidad


class EspecialidadSeeder:
    def __init__(self, db):
        self.db = db

    def run(self):
        print("🌱 Poblando especialidades...")
        try:
            contador_nuevos = 0
            
            # Obtener especialidades existentes en una sola consulta para optimizar
            existing_enums = {e.nombre for e in self.db.session.scalars(select(Especialidad))}

            # Iteramos directamente sobre los miembros del Enum
            for miembro_enum in TipoEspecialidad:
                if miembro_enum not in existing_enums:
                    nueva_especialidad = Especialidad(nombre=miembro_enum)
                    self.db.session.add(nueva_especialidad)
                    contador_nuevos += 1

            if contador_nuevos > 0:
                self.db.session.commit()
                print(f"✅ Especialidades pobladas con éxito ({contador_nuevos} nuevas).")
            else:
                print("💡 Especialidades ya existentes, no se realizaron cambios.")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error al poblar especialidades: {e}")