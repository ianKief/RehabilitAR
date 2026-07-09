import random
from src.core.salas.salas import Sala

class SalaSeeder:
    def __init__(self, db):
        self.db = db

    def run(self):
        print("🌱 Poblando salas...")
        try:
            # Si ya existen salas, no hacemos nada para que sea idempotente
            if self.db.session.query(Sala).first():
                print("💡 Salas ya existentes, no se realizaron cambios.")
                return

            numeros_puerta_unicos = range(1, 6)
            salas_a_crear = []
            for numero in numeros_puerta_unicos:
                numero_str = str(numero)
                capacidad_aleatoria = random.randint(1, 50)
                descripcion_dinamica = f"Sala-{numero_str}"

                salas_a_crear.append(Sala(
                    numero_puerta=numero_str,
                    descripcion=descripcion_dinamica,
                    capacidad=capacidad_aleatoria,
                    estado="HABILITADA"
                ))

            self.db.session.add_all(salas_a_crear)
            self.db.session.commit()
            print(f"✅ Salas pobladas con éxito ({len(salas_a_crear)} nuevas).")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error al poblar salas: {e}")