import random
import datetime

from src.core.usuarios.usuarios import Cliente, EstadoUsuario


class EstadisticasSeeder:

    def __init__(self, db):
        self.db = db

    def run(self):
        print("🌱 Creando usuarios para estadísticas...")

        try:
            usuarios = []

            nombres = [
                "Juan", "Pedro", "Ana", "Lucia", "Carlos",
                "Maria", "Sofia", "Martin", "Laura", "Diego"
            ]

            apellidos = [
                "Gomez", "Perez", "Rodriguez", "Fernandez",
                "Lopez", "Garcia", "Martinez"
            ]

            id_usuario = 0

            # Cantidad de clientes por año
            clientes_por_anio = {
                2020: 10,
                2021: 12,
                2022: 18,
                2023: 20,
                2024: 15,
                2025: 25,
                2026: 20
            }

            for anio, cantidad in clientes_por_anio.items():
                for _ in range(cantidad):
                    usuarios.append(
                        self.crear_cliente(
                            id_usuario,
                            random.choice(nombres),
                            random.choice(apellidos),
                            anio
                        )
                    )
                    id_usuario += 1

            self.db.session.add_all(usuarios)
            self.db.session.commit()

            print("✅ Clientes creados para estadísticas.")

        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error creando usuarios de estadísticas: {e}")

    def crear_cliente(self, i, nombre, apellido, anio):

        hoy = datetime.datetime.now()

        # Si es el año actual, no generar meses futuros
        if anio == hoy.year:
            mes_maximo = hoy.month
        else:
            mes_maximo = 12

        mes = random.randint(1, mes_maximo)

        # Si es el mes actual, no generar días futuros
        if anio == hoy.year and mes == hoy.month:
            dia_maximo = hoy.day
        else:
            dia_maximo = 28

        fecha_creacion = datetime.datetime(
            anio,
            mes,
            random.randint(1, dia_maximo)
        )

        return Cliente(
            nombre=nombre,
            apellido=apellido,
            dni=f"{random.randint(10000000, 99999999)}",
            email=f"estadistica{i}@gmail.com",
            password="123456",
            estado=EstadoUsuario.ACTIVO,
            direccion=f"Calle falsa {i}",
            telefono=f"11223344{i}",
            fecha_nacimiento=datetime.datetime(
                random.randint(1980, 2000),
                random.randint(1, 12),
                random.randint(1, 28)
            ),
            fecha_creacion=fecha_creacion
        )