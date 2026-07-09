import random
from datetime import date, time, timedelta
from sqlalchemy import select
from src.core.clases import Clase
from src.core.usuarios import Usuario, ProfesorDictaClase
from src.core.usuarios.usuarios import Especialidad
from src.core.salas.salas import Sala, EstadoSala
from src.core.usuarios.usuarios import RolUsuario

class ClaseSeeder:
    def __init__(self, db):
        self.db = db

        # Horarios de inicio de clase
        self.horarios_prueba = [
            time(8, 0), time(9, 30), time(11, 0), 
            time(14, 30), time(16, 0), time(17, 30)
        ]

    def run(self):
        print("🌱 Poblando clases (con asignación directa de profesor)...")
        try:
            # Si ya existen clases, no hacemos nada para que sea idempotente
            if self.db.session.query(Clase).first():
                print("💡 Clases ya existentes, no se realizaron cambios.")
                return

            # Optimizamos consultas: traemos los datos necesarios en lugar de cargar todos los objetos pesados a la memoria
            ids_salas = list(self.db.session.scalars(select(Sala.id).filter_by(eliminada=False)))
            ids_profesores = list(self.db.session.scalars(select(Usuario.id).filter_by(rol=RolUsuario.PROFESOR)))
            
            # Obtenemos las especialidades reales de la base de datos
            especialidades_db = list(self.db.session.scalars(select(Especialidad)))
            if not especialidades_db:
                print("⚠️ Error: No se encontraron especialidades en la BD. Ejecutá primero el EspecialidadSeeder.")
                return

            # Nombres de clases por especialidad (usando el valor del Enum como clave)
            nombres_por_especialidad = {
                "TREN SUPERIOR": ["Rehabilitación de Hombro", "Fortalecimiento Cervical", "Post-Quirúrgico de Codo/Muñeca"],
                "TREN INFERIOR": ["Rehabilitación de Rodilla", "Estabilidad de Tobillo", "Fisioterapia de Cadera"],
                "TREN MEDIO": ["Estabilización de Core", "Reeducación Postural Lumbar", "Gimnasia Correctiva de Columna"]
            }

            hoy = date.today()
            # Encontramos el lunes de la semana actual
            lunes_esta_semana = hoy - timedelta(days=hoy.weekday())

            # Lista para almacenar las clases y procesar las relaciones en bloque
            clases_y_profesores = []

            for dia_semana in range(5):  # 0 a 4 (Lunes a Viernes)
                fecha_base = lunes_esta_semana + timedelta(days=dia_semana)

                # Seleccionamos horarios distintos para no superponer clases en el mismo día
                horarios_del_dia = random.sample(self.horarios_prueba, 4)
                
                # 2 Clases Fijas (se repiten 4 semanas a la misma hora)
                for i in range(2):
                    especialidad_obj = random.choice(especialidades_db)
                    especialidad_nombre_enum = especialidad_obj.nombre # Esto es el Enum
                    nombre = random.choice(nombres_por_especialidad[especialidad_nombre_enum.value])
                    horario = horarios_del_dia[i]
                    duracion = random.choice([45, 60, 90])
                    id_sala_asignada = random.choice(ids_salas) if ids_salas else None
                    
                    # Asignamos el profesor fuera del bucle de semanas para que la clase Fija mantenga siempre al mismo profesor y sala.
                    id_profesor_asignado = random.choice(ids_profesores) if ids_profesores else None

                    for semana in range(4):
                        fecha_clase = fecha_base + timedelta(weeks=semana)
                        clase = Clase(
                            nombre=nombre,
                            especialidad=especialidad_nombre_enum.value, # Asignamos el valor del Enum (string)
                            duracion=duracion,
                            descripcion=f"Sesión enfocada en {especialidad_nombre_enum.value.lower()}. Trabajo de movilidad y fuerza progresiva. Tipo: Fija.",
                            suspendida=False,
                            fecha_clase=fecha_clase,
                            horario=horario,
                            aprobada=True,
                            tipo="Fija",
                            sala_id=id_sala_asignada
                        )
                        self.db.session.add(clase)
                        clases_y_profesores.append((clase, id_profesor_asignado, "Fija"))

                # 2 Clases Individuales por semana (horarios distintos a las fijas de ese día)
                for semana in range(4):
                    fecha_clase = fecha_base + timedelta(weeks=semana)
                    for i in range(2, 4):
                        especialidad_obj = random.choice(especialidades_db)
                        especialidad_nombre_enum = especialidad_obj.nombre # Esto es el Enum
                        nombre = random.choice(nombres_por_especialidad[especialidad_nombre_enum.value])
                        horario = horarios_del_dia[i]
                        duracion = random.choice([45, 60, 90])
                        id_sala_asignada = random.choice(ids_salas) if ids_salas else None
                        
                        id_profesor_asignado = random.choice(ids_profesores) if ids_profesores else None
                        clase = Clase(
                            nombre=nombre,
                            especialidad=especialidad_nombre_enum.value, # Asignamos el valor del Enum (string)
                            duracion=duracion,
                            descripcion=f"Sesión enfocada en {especialidad_nombre_enum.value.lower()}. Trabajo de movilidad y fuerza progresiva. Tipo: Individual.",
                            suspendida=False,
                            fecha_clase=fecha_clase,
                            horario=horario,
                            aprobada=True,
                            tipo="Individual",
                            sala_id=id_sala_asignada
                        )
                        self.db.session.add(clase)
                        clases_y_profesores.append((clase, id_profesor_asignado, "Individual"))

            # Realizamos un único flush para obtener los IDs generados de todas las clases insertadas a la vez
            self.db.session.flush()

            # Insertamos en bloque las relaciones profesor-clase
            for clase, id_profesor, tipo in clases_y_profesores:
                if id_profesor:
                    self.db.session.add(ProfesorDictaClase(
                        id_profesor=id_profesor,
                        id_clase=clase.id
                    ))

            sala_de_clase_sin_profesor = Sala (
                numero_puerta = "1010",
                descripcion = "Para alojar una clase sin profesor asignado",
                capacidad = 10,
                estado = EstadoSala.HABILITADA,
                eliminada = False
            )
            self.db.session.add(sala_de_clase_sin_profesor)

            sala_de_clase_sin_profesor2 = Sala (
                numero_puerta = "1011",
                descripcion = "Para alojar otra clase sin profesor asignado",
                capacidad = 10,
                estado = EstadoSala.HABILITADA,
                eliminada = False
            )
            self.db.session.add(sala_de_clase_sin_profesor2)
            self.db.session.flush()

            clase_sin_profesor = Clase (
                nombre = "Clase sin profesor",
                especialidad = "Tren Superior",
                duracion = 120,
                descripcion = "Esta es una clase que no tiene un profesor asignado",
                fecha_clase = date(year=2026, month=7, day=27),
                horario = time(hour = 10),
                aprobada = True,
                tipo = "Individual",
                sala = sala_de_clase_sin_profesor
            )
            self.db.session.add(clase_sin_profesor)

            # Esto es para comprobar la condición de anotarse a la vez
            clase_sin_profesor2 = Clase (
                nombre = "Clase sin profesor2",
                especialidad = "Tren Superior",
                duracion = 120,
                descripcion = "Esto sirve para comprobar si me puedo anotar a dos clases a la vez",
                fecha_clase = date(year=2026, month=7, day=27),
                horario = time(hour = 10),
                aprobada = True,
                tipo = "Individual",
                sala = sala_de_clase_sin_profesor2
            )
            self.db.session.add(clase_sin_profesor2)

            # Esto es para comprobar la condición de sala ocupada todo el día
            sala_re_llena_el_30_7 = Sala (
                numero_puerta = "Ocupado el 30/7",
                descripcion = "Para comprobar condiciones en salas ocupadas",
                capacidad = 10,
                estado = EstadoSala.HABILITADA,
                eliminada = False
            )
            self.db.session.add(sala_re_llena_el_30_7)
            self.db.session.flush()
            
            clase_que_ocupa_todo_el_dia = Clase (
                nombre = "Clase DEMASIADO LARGA",
                especialidad = "Tren Superior",
                duracion = 720,
                descripcion = "Esta es una clase que no tiene un profesor asignado",
                fecha_clase = date(year=2026, month=7, day=30),
                horario = time(hour = 8),
                aprobada = True,
                tipo = "Individual",
                sala = sala_re_llena_el_30_7
            )
            self.db.session.add(clase_que_ocupa_todo_el_dia)

            self.db.session.commit()
            print(f"✅ Clases pobladas con éxito ({len(clases_y_profesores)} instancias).")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error al poblar clases: {e}")


class ProfesorDictaClaseSeeder ():
    """NOTA: según las HU #90 y #91, se considera especialidad a las 3 de arriba."""
    def __init__(self, db):
        self.db = db
    
    def run (self):
        # La asignación de profesores ahora se maneja directamente en ClaseSeeder.
        # Esto garantiza que las clases fijas mantengan al mismo profesor en todas sus repeticiones,
        # y simplifica enormemente la lógica de disponibilidad sin generar fallos en la base de datos.
        pass