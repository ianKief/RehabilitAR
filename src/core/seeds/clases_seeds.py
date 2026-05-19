import random
from datetime import date, time, timedelta
from src.core.clases import Clase  # El import de tu modelo de clases

class ClaseSeeder:
    def __init__(self, db):
        self.db = db
        # Especialidades
        self.especialidades = ["Tren Superior", "Tren Inferior", "Tren Medio"]
        self.tipos_clases = ["Fija", "Individual"]
        
        # Nombres de clases
        self.nombres_por_especialidad = {
            "Tren Superior": ["Rehabilitación de Hombro", "Fortalecimiento Cervical", "Post-Quirúrgico de Codo/Muñeca"],
            "Tren Inferior": ["Rehabilitación de Rodilla", "Estabilidad de Tobillo", "Fisioterapia de Cadera"],
            "Tren Medio": ["Estabilización de Core", "Reeducación Postural Lumbar", "Gimnasia Correctiva de Columna"]
        }

        # Horarios de inicio de clase
        self.horarios_prueba = [
            time(8, 0), time(9, 30), time(11, 0), 
            time(14, 30), time(16, 0), time(17, 30)
        ]

    def run(self):
        print("Insertando clases de prueba")

        hoy = date.today()

        # Generamos 8 clases distribuidas en los próximos días
        for i in range(8):
            especialidad = random.choice(self.especialidades)
            nombre = random.choice(self.nombres_por_especialidad[especialidad])
            tipo = random.choice(self.tipos_clases)
            horario = random.choice(self.horarios_prueba)
            
            # Repartimos las clases entre hoy, mañana y pasado
            dias_en_adelante = random.randint(0, 2)
            fecha_clase = hoy + timedelta(days=dias_en_adelante)

            clase = Clase(
                nombre=nombre,
                especialidad=especialidad,
                duracion=random.choice([45, 60, 90]),  # Minutos
                capacidad_maxima=random.randint(5, 12),
                descripcion=f"Sesión enfocada en {especialidad.lower()}. Trabajo de movilidad y fuerza progresiva. Tipo: {tipo}.",
                suspendida=False,
                fecha_clase=fecha_clase,
                horario=horario,
                aprobada=True,
                tipo=tipo
            )

            print(f"Creada: {clase.nombre} -> Especialidad: {clase.especialidad} | {clase.fecha_clase} {clase.horario}")
            self.db.session.add(clase)

        self.db.session.commit()
        print("¡Se han guardado las clases correctamente!")