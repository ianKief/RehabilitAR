from sqlalchemy import select
from src.core.usuarios.usuarios import Especialidad, TipoEspecialidad


class EspecialidadSeeder:
    def __init__(self, db):
        self.db = db

    def run(self):
        print("Insertando especialidades base...")

        contador_nuevos = 0

        # Iteramos directamente sobre los miembros del Enum
        for miembro_enum in TipoEspecialidad:
            # Validamos si ya existe para hacerlo idempotente y evitar duplicados
            query = select(Especialidad).filter_by(nombre=miembro_enum)
            especialidad_existente = self.db.session.scalars(query).first()

            if not list(self.db.session.scalars(query)): # O usando scalar() de forma directa
                nueva_especialidad = Especialidad(nombre=miembro_enum)
                self.db.session.add(nueva_especialidad)
                contador_nuevos += 1
                print(f" -> Seeder: Preparada especialidad {miembro_enum.value}")

        # Confirmamos los cambios de manera atómica
        if contador_nuevos > 0:
            try:
                self.db.session.commit()
                print(f"¡Se han guardado {contador_nuevos} especialidades correctamente!")
            except Exception as e:
                self.db.session.rollback()
                print(f"❌ Error al ejecutar el commit del seeder: {e}")
        else:
            print("💡 Las especialidades ya estaban inicializadas. No se realizaron cambios.")