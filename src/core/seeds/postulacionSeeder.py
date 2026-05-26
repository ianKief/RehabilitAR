import random
from sqlalchemy import select
from src.core.profesores.profesores import Profesor
from src.core.database import db
from src.core.clases.clases import Clase, PostulacionClase, ClaseBloque

class PostulacionSeeder:
    def __init__(self, db):
        self.db = db

    def run(self):
        print("Insertando postulaciones de prueba en estado PENDIENTE...")

        # 1. Traer todos los profesores reales con sus IDs y nombres de especialidad (en texto)
        # Cruzamos Profesor con Especialidad para saber a qué área pertenece cada uno
        # (Asumo que en el modelo Profesor podés acceder a la Especialidad o filtrar por su id)
        query_profesores = select(Profesor)
        profesores_reales = self.db.session.scalars(query_profesores).all()

        if not profesores_reales:
            print("⚠️ Error: No hay profesores en la BD para generar postulaciones.")
            return

        # 2. Traer todas las clases creadas por el ClaseSeeder
        query_clases = select(Clase)
        clases_disponibles = self.db.session.scalars(query_clases).all()

        if not clases_disponibles:
            print("⚠️ Error: No hay clases en la BD.")
            return

        # 3. Mapear qué clases pertenecen a cada bloque para resolver la recurrencia fija de forma masiva
        query_bloques = select(ClaseBloque)
        relaciones_bloque = self.db.session.scalars(query_bloques).all()
        
        # Diccionario auxiliar: { id_clase: id_bloque }
        clase_a_bloque = {rb.id_clase: rb.id_bloque for rb in relaciones_bloque}
        
        # Diccionario inverso para buscar rápido: { id_bloque: [id_clase1, id_clase2, ...] }
        bloque_a_clases = {}
        for rb in relaciones_bloque:
            bloque_a_clases.setdefault(rb.id_bloque, []).append(rb.id_clase)

        # Para llevar registro de a qué clases/bloques ya postulamos a un profesor y evitar duplicados en el loop
        # Guardamos tuplas: (profesor_id, clase_id) o (profesor_id, f"bloque_{id_bloque}")
        procesados = set()

        # Nombres de las especialidades mapeados a sus IDs según tu ProfesorSeeder
        # ID 1: Tren Superior, ID 2: Tren Inferior, ID 3: Tren Medio
        mapa_especialidades = {
            1: "Tren Superior",
            2: "Tren Inferior",
            3: "Tren Medio"
        }

        # 4. Empezamos el bucle de asignación inteligente
        for clase in clases_disponibles:
            # Buscamos qué profesores comparten la especialidad exacta de esta clase
            profes_aptos = [
                p for p in profesores_reales 
                if mapa_especialidades.get(p.especialidad_id) == clase.especialidad
            ]

            if not profes_aptos:
                continue

            # Elegimos al azar 1 o 2 profesores aptos para que compitan por esta vacante
            cant_postulantes = min(len(profes_aptos), random.randint(1, 2))
            profes_seleccionados = random.sample(profes_aptos, k=cant_postulantes)

            for profe in profes_seleccionados:
                profesor_id = profe.id_usuario  # O profe.id según tu clave primaria

                # Caso A: La clase es FIJA y pertenece a un bloque recurrente
                if clase.tipo == "Fija" and clase.id in clase_a_bloque:
                    id_bloque_actual = clase_a_bloque[clase.id]
                    llave_bloque = (profesor_id, f"bloque_{id_bloque_actual}")

                    # Si este profesor ya fue postulado a este bloque entero en una iteración previa, lo salteamos
                    if llave_bloque in procesados:
                        continue

                    # Buscamos todas las clases asociadas a ese mismo bloque (Semana 1, Semana 2, etc.)
                    ids_clases_del_bloque = bloque_a_clases.get(id_bloque_actual, [])

                    for c_id in ids_clases_del_bloque:
                        postulacion_fija = PostulacionClase(
                            clase_id=c_id,
                            profesor_id=profesor_id,
                            estado="PENDIENTE"  # 🔥 ESTRICTAMENTE PENDIENTE
                        )
                        self.db.session.add(postulacion_fija)
                    
                    procesados.add(llave_bloque)
                    print(f" -> [BLOQUE FIJO] Profe #{profesor_id} postulado a las {len(ids_clases_del_bloque)} instancias del Bloque: {id_bloque_actual} ({clase.especialidad})")

                # Caso B: La clase es INDIVIDUAL
                elif clase.tipo == "Individual":
                    llave_individual = (profesor_id, clase.id)
                    
                    if llave_individual in procesados:
                        continue

                    postulacion_individual = PostulacionClase(
                        clase_id=clase.id,
                        profesor_id=profesor_id,
                        estado="PENDIENTE"  #  ESTRICTAMENTE PENDIENTE
                    )
                    self.db.session.add(postulacion_individual)
                    
                    procesados.add(llave_individual)
                    print(f" -> [INDIVIDUAL] Profe #{profesor_id} postulado a clase ID: {clase.id} ({clase.especialidad})")

        # 5. Guardamos de forma segura en la base de datos
        try:
            self.db.session.commit()
            print("¡Seeder de postulaciones pendientes e inteligentes completado con éxito!")
        except Exception as e:
            self.db.session.rollback()
            print(f" Error al ejecutar el commit de postulaciones: {e}")