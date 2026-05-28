from src.core.usuarios.usuarios import Especialidad, Profesor, RolUsuario, TipoEspecialidad, Usuario

class ProfesorSeeder:
    def __init__(self, db):
        self.db = db
        # 🔄 CAMBIO: Mapeamos los textos viejos a los miembros reales del Enum de tu compañero
        self.especialidades_mapeadas = [
            {"id": 1, "enum_val": TipoEspecialidad.SUPERIOR},  # "TREN SUPERIOR"
            {"id": 2, "enum_val": TipoEspecialidad.INFERIOR},  # "TREN INFERIOR"
            {"id": 3, "enum_val": TipoEspecialidad.MEDIO}      # "TREN MEDIO"
        ]

    def run(self):
        print("Insertando especialidades y cuerpo docente (Jerarquía de Herencia)...")

        # 1. Poblar la tabla de especialidades mapeando el Enum de tu compañero
        for esp_data in self.especialidades_mapeadas:
            especialidad = self.db.session.get(Especialidad, esp_data["id"])
            if not especialidad:
                especialidad = Especialidad(id=esp_data["id"], nombre=esp_data["enum_val"])
                self.db.session.add(especialidad)
                print(f" -> Seeder: Especialidad '{esp_data['enum_val'].value}' configurada con ID: {esp_data['id']}")

        # Sincronizamos la sesión antes de avanzar
        self.db.session.flush()

        # 📝 CONFIGURACIÓN DE DOCENTES A CREAR
        # 🔄 CAMBIO: especialidad_id pasa a ser id_especialidad para acoplarse al nuevo modelo
        profesores_a_crear = [
            {"id": 2, "nombre": "Gero", "apellido": "Docente", "email": "profesor@rehabilitar.com", "id_especialidad": 2}, 
            {"id": 3, "nombre": "Carlos", "apellido": "Kinesiologo", "email": "carlos@rehabilitar.com", "id_especialidad": 1}, 
            {"id": 4, "nombre": "Ana", "apellido": "Fisiatra", "email": "ana@rehabilitar.com", "id_especialidad": 3},  
            {"id": 5, "nombre": "Mariano", "apellido": "Gómez", "email": "mariano@rehabilitar.com", "id_especialidad": 2}, 
            {"id": 6, "nombre": "Laura", "apellido": "Sánchez", "email": "laura@rehabilitar.com", "id_especialidad": 1},   
            {"id": 7, "nombre": "Julia", "apellido": "Pérez", "email": "julia@rehabilitar.com", "id_especialidad": 3},     
        ]

        for p_data in profesores_a_crear:
            # 2. 🔄 CAMBIO CRÍTICO: Buscamos e instanciamos directamente al modelo SUBCLASE 'Profesor'
            profesor_registro = self.db.session.get(Profesor, p_data["id"])
            
            if not profesor_registro:
                # Al instanciar Profesor, le enviamos tanto los campos que hereda de Usuario 
                # como los campos propios de su tabla de profesores.
                profesor_registro = Profesor(
                    id=p_data["id"],                      # PK unificada
                    nombre=p_data["nombre"],
                    apellido=p_data["apellido"],
                    email=p_data["email"],
                    password="scrypt:unapasswordcualquiera",
                    rol=RolUsuario.PROFESOR,              # Identidad polimórfica del Enum
                    id_especialidad=p_data["id_especialidad"]  # Campo propio de Profesor
                )
                self.db.session.add(profesor_registro)
                print(f" -> Seeder: Creado Profesor Polimórfico ID: {p_data['id']} ({p_data['nombre']}) -> Especialidad: {p_data['id_especialidad']}")

        # Consolidamos la transacción de forma segura
        try:
            self.db.session.commit()
            print("¡Se han guardado todos los profesores polimórficos de forma limpia!")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error en ProfesorSeeder: {e}")