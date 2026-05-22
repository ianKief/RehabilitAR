import random
from datetime import date, time, timedelta

from sqlalchemy import or_, and_, text
from sqlalchemy.orm import aliased

from src.core.clases import Clase, listar_clases  # El import de tu modelo de clases
from src.core.usuarios import Usuario, ProfesorDictaClase

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


class ProfesorDictaClaseSeeder ():
    """NOTA: según las HU #90 y #91, se considera especialidad a las 3 de arriba."""
    def __init__(self, db):
        self.db = db

        self.especialidades = ["Tren Superior", "Tren Inferior", "Tren Medio"]
        self.tipos_clases = ["Fija", "Individual"]
        
        # Nombres de clases
        self.nombres_por_especialidad = {
            "Tren Superior": ["Rehabilitación de Hombro", "Fortalecimiento Cervical", "Post-Quirúrgico de Codo/Muñeca"],
            "Tren Inferior": ["Rehabilitación de Rodilla", "Estabilidad de Tobillo", "Fisioterapia de Cadera"],
            "Tren Medio": ["Estabilización de Core", "Reeducación Postural Lumbar", "Gimnasia Correctiva de Columna"]
        }
    
    def conseguir_profesor_con_disponibilidad (self, clase):
        Profesor = aliased(Usuario)

        query = (self.db.session.query(Profesor)
            .outerjoin (ProfesorDictaClase, Profesor.id == ProfesorDictaClase.id_profesor)
            .outerjoin (Clase, Clase.id == ProfesorDictaClase.id_clase)
            .filter(or_((clase.fecha_clase != Clase.fecha_clase), (and_((clase.horario < Clase.horario), (clase.horario + (clase.duracion * text("INTERVAL '1 minute'") < Clase.horario)))), (and_((clase.horario > Clase.horario), (clase.horario > Clase.horario + (clase.duracion * text("INTERVAL '1 minute'")))))))
            # Acá debería filtrar por tren, si el profesor tuviese alguno
        )

        return self.db.session.scalars(query).one_or_none()

    """Limitaciones a tener en cuenta:
    1. La especialidad del profesor debe coincidir con la especialidad de la clase
    2. El profesor debe tener el horario disponible"""
    def run (self):
        clases = listar_clases ()
        for clase in clases:
            profesor = self.conseguir_profesor_con_disponibilidad (clase)
            if profesor != None:
                profesor_clase = ProfesorDictaClase(
                    id_profesor = profesor.id,
                    id_clase = clase.id
                )
                self.db.session.add(profesor_clase)

        self.db.session.commit()
