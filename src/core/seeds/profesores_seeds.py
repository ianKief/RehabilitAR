# src/core/seeds/profesores_seeds.py


from src.core.usuarios.usuarios import Usuario
from src.core.profesores.profesores import Especialidad, Profesor


class ProfesorSeeder:
    def __init__(self, db):
        self.db = db
        # Mantenemos las mismas especialidades exactas del ClaseSeeder
        self.especialidades_nombres = ["Tren Superior", "Tren Inferior", "Tren Medio"]

    def run(self):
        print("Insertando especialidades y cuerpo docente de prueba...")

        # 1. Poblar la tabla de especialidades de forma secuencial (ID 1, 2 y 3)
        for i, nombre_esp in enumerate(self.especialidades_nombres, start=1):
            especialidad = self.db.session.get(Especialidad, i)
            if not especialidad:
                especialidad = Especialidad(id=i, nombre=nombre_esp)
                self.db.session.add(especialidad)
                print(f" -> Seeder: Especialidad '{nombre_esp}' configurada con ID: {i}")

        # Forzamos un flush para asegurarnos de que los IDs de las especialidades existan en la sesión
        self.db.session.flush()

        # 📝 CONFIGURACIÓN DE DOCENTES A CREAR
        # Mantenemos fijo el ID 2 para tus pruebas de controlador y agregamos el 3 y 4
        profesores_a_crear = [
            {"id": 2, "nombre": "Gero", "apellido": "Docente", "email": "profesor@rehabilitar.com", "especialidad_id": 2}, # Tren Inferior
            {"id": 3, "nombre": "Carlos", "apellido": "Kinesiologo", "email": "carlos@rehabilitar.com", "especialidad_id": 1}, # Tren Superior
            {"id": 4, "nombre": "Ana", "apellido": "Fisiatra", "email": "ana@rehabilitar.com", "especialidad_id": 3},  # Tren Medio
            {"id": 5, "nombre": "Mariano", "apellido": "Gómez", "email": "mariano@rehabilitar.com", "especialidad_id": 2}, # Tren Inferior
            {"id": 6, "nombre": "Laura", "apellido": "Sánchez", "email": "laura@rehabilitar.com", "especialidad_id": 1},   # Tren Superior
            {"id": 7, "nombre": "Julia", "apellido": "Pérez", "email": "julia@rehabilitar.com", "especialidad_id": 3},     # Tren Medio
        ]

        for p_data in profesores_a_crear:
            # 2. Crear o recuperar el Usuario puro
            usuario_profe = self.db.session.get(Usuario, p_data["id"])
            if not usuario_profe:
                usuario_profe = Usuario(
                    id=p_data["id"],
                    nombre=p_data["nombre"],
                    apellido=p_data["apellido"],
                    email=p_data["email"],
                    password="scrypt:unapasswordcualquiera",
                    rol="PROFESOR"
                )
                self.db.session.add(usuario_profe)
                print(f" -> Seeder: Creado Usuario base ID: {p_data['id']} ({p_data['nombre']}) con rol PROFESOR")
            
            self.db.session.flush()

            # 3. Vincular al usuario directo en la tabla profesores asignando su especialidad correspondiente
            profesor_registro = self.db.session.get(Profesor, p_data["id"])
            if not profesor_registro:
                # Si tu tabla de profesores usa id_usuario como PK o FK, calza perfecto acá
                profesor_registro = Profesor(
                    id_usuario=p_data["id"],
                    especialidad_id=p_data["especialidad_id"]
                )
                self.db.session.add(profesor_registro)
                print(f" -> Seeder: Registro insertado en tabla 'profesores' (User ID: {p_data['id']} -> Esp ID: {p_data['especialidad_id']})")

        # Consolidamos el bloque completo en Postgres
        try:
            self.db.session.commit()
            print("¡Se han guardado todos los profesores y especialidades reales de forma limpia!")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error en ProfesorSeeder: {e}")