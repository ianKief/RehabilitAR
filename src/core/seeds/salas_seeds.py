import random
from src.core.salas.salas import Sala

class SalaSeeder:
    def __init__(self, db):
        self.db = db

    def run(self):
        print("Insertando 5 salas de prueba...")

        numeros_puerta_unicos = range(1, 6)

        for numero in numeros_puerta_unicos:
            numero_str = str(numero)
            capacidad_aleatoria = random.randint(1, 50)
            descripcion_dinamica = f"Sala-{numero_str}"

            sala = Sala(
                numero_puerta=numero_str,
                descripcion=descripcion_dinamica,
                capacidad=capacidad_aleatoria,
                estado="HABILITADA"
            )

            self.db.session.add(sala)

        self.db.session.commit()
        print("¡Se han guardado las 5 salas con éxito!")