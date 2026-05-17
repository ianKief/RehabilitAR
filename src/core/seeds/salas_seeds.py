import random
from src.core.salas.salas import Sala

class SalaSeeder:
    def __init__(self, db):
        self.db = db
        self.estados = ["HABILITADA", "DESHABILITADA"]

    def run(self):
        print("Insertando 10 salas de prueba...")

        numeros_puerta_unicos = random.sample(range(100, 1000), 10)

        for numero in numeros_puerta_unicos:
            numero_str = str(numero)
            capacidad_aleatoria = random.randint(1, 50)
            estado_aleatorio = random.choice(self.estados)
            descripcion_dinamica = f"Sala-{numero_str}"

            sala = Sala(
                numero_puerta=numero_str,
                descripcion=descripcion_dinamica,
                capacidad=capacidad_aleatoria,
                estado=estado_aleatorio
            )

            print(f"Creada: {sala.numero_puerta}")

            self.db.session.add(sala)

        self.db.session.commit()
        print("¡Se han guardado las 10 salas con éxito!")