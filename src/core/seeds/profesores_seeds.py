import random
from src.core.usuarios.usuarios import Profesor

class ProfesorSeeder:
    def __init__(self, db):
        self.db = db
        # Mapeo oficial de especialidades del sistema
        # Como tu columna es 'id_especialidad' (Integer), usamos directamente los IDs
        self.especialidades_mapeadas = [
            {"id": 1, "nombre": "TREN SUPERIOR"},
            {"id": 2, "nombre": "TREN INFERIOR"},
            {"id": 3, "nombre": "TREN MEDIO"}
        ]

    def run(self):
        print("Buscando profesores creados para asignarles sus IDs de especialidad...")

        # 1. Traemos todos los profesores de la base de datos
        profesores = self.db.session.query(Profesor).all()

        if not profesores:
            print("⚠️ Advertencia: No se encontraron profesores en la BD. Ejecutá primero el UsuarioSeeder.")
            return

        contador_actualizados = 0

        for profe in profesores:
            # 2. Controlamos si el profesor no tiene el id_especialidad asignado
            if profe.id_especialidad is None:
                
                # Elegimos un mapa aleatorio de nuestra lista de especialidades
                mapeo_elegido = random.choice(self.especialidades_mapeadas)
                
                # 🎯 ASIGNACIÓN CLAVE: Modificamos directamente el campo de la clave foránea (id_especialidad)
                profe.id_especialidad = mapeo_elegido["id"]
                
                print(f" -> Profesor {profe.nombre} {profe.apellido} (ID: {profe.id}) acoplado a Especialidad ID: {profe.id_especialidad} ({mapeo_elegido['nombre']})")
                contador_actualizados += 1

        # 3. Guardamos los cambios de forma segura en Postgres
        if contador_actualizados > 0:
            try:
                self.db.session.commit()
                print(f"¡Se han actualizado {contador_actualizados} profesores en la tabla 'profesores' con sus claves foráneas con éxito!")
            except Exception as e:
                self.db.session.rollback()
                print(f"❌ Error al ejecutar el commit en ProfesorEspecialidadSeeder: {e}")
        else:
            print("Todos los profesores ya tenían una especialidad asociada (id_especialidad != None).")