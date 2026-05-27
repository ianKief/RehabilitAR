import random
from datetime import date, time, timedelta

from sqlalchemy import or_, and_, func, literal_column
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
        print("Insertando clases de prueba de Lunes a Viernes por un mes...")

        hoy = date.today()
        # Encontramos el lunes de la semana actual
        lunes_esta_semana = hoy - timedelta(days=hoy.weekday())

        for dia_semana in range(5):  # 0 a 4 (Lunes a Viernes)
            fecha_base = lunes_esta_semana + timedelta(days=dia_semana)

            # Seleccionamos horarios distintos para no superponer clases en el mismo día
            horarios_del_dia = random.sample(self.horarios_prueba, 4)
            
            # 2 Clases Fijas (se repiten 4 semanas a la misma hora)
            for i in range(2):
                especialidad = random.choice(self.especialidades)
                nombre = random.choice(self.nombres_por_especialidad[especialidad])
                horario = horarios_del_dia[i]
                duracion = random.choice([45, 60, 90])
                capacidad = random.randint(5, 12)
                
                for semana in range(4):
                    fecha_clase = fecha_base + timedelta(weeks=semana)
                    clase = Clase(
                        nombre=nombre,
                        especialidad=especialidad,
                        duracion=duracion,
                        capacidad_maxima=capacidad,
                        descripcion=f"Sesión enfocada en {especialidad.lower()}. Trabajo de movilidad y fuerza progresiva. Tipo: Fija.",
                        suspendida=False,
                        fecha_clase=fecha_clase,
                        horario=horario,
                        aprobada=True,
                        tipo="Fija"
                    )
                    self.db.session.add(clase)
                    print(f"Creada: {clase.nombre} -> Especialidad: {clase.especialidad} | {clase.fecha_clase} {clase.horario} | Fija")

            # 2 Clases Individuales por semana (horarios distintos a las fijas de ese día)
            for semana in range(4):
                fecha_clase = fecha_base + timedelta(weeks=semana)
                for i in range(2, 4):
                    especialidad = random.choice(self.especialidades)
                    nombre = random.choice(self.nombres_por_especialidad[especialidad])
                    horario = horarios_del_dia[i]
                    duracion = random.choice([45, 60, 90])
                    capacidad = random.randint(5, 12)
                    
                    clase = Clase(
                        nombre=nombre,
                        especialidad=especialidad,
                        duracion=duracion,
                        capacidad_maxima=capacidad,
                        descripcion=f"Sesión enfocada en {especialidad.lower()}. Trabajo de movilidad y fuerza progresiva. Tipo: Individual.",
                        suspendida=False,
                        fecha_clase=fecha_clase,
                        horario=horario,
                        aprobada=True,
                        tipo="Individual"
                    )
                    self.db.session.add(clase)
                    print(f"Creada: {clase.nombre} -> Especialidad: {clase.especialidad} | {clase.fecha_clase} {clase.horario} | Individual")

        self.db.session.commit()
        print("¡Se han guardado las clases correctamente!")


class ProfesorDictaClaseSeeder ():
    """NOTA: según las HU #90 y #91, se considera especialidad a las 3 de arriba."""
    def __init__(self, db):
        self.db = db
    
    def conseguir_profesor_con_disponibilidad (self, clase):
        Profesor = aliased(Usuario)

        query = (self.db.session.query(Profesor)
            .outerjoin (ProfesorDictaClase, Profesor.id == ProfesorDictaClase.id_profesor)
            .outerjoin (Clase, Clase.id == ProfesorDictaClase.id_clase)
            .filter(or_((clase.fecha_clase != Clase.fecha_clase), (and_((clase.horario < Clase.horario), (clase.horario +  (clase.duracion * literal_column("INTERVAL '1 minute'")) < Clase.horario))), (and_((clase.horario > Clase.horario), (clase.horario > Clase.horario + (clase.duracion * literal_column("INTERVAL '1 minute'")))))))
            # Acá debería filtrar por tren, si el profesor tuviese alguno
        )

        return self.db.session.scalars(query).one_or_none()

    """Limitaciones a tener en cuenta:
    1. La especialidad del profesor debe coincidir con la especialidad de la clase
    2. El profesor debe tener el horario disponible
    Es ideal que haya más profesores que clases"""
    def run (self):
        print ("Creando tantas relaciones entre clases con profesores como clases haya...")
        clases = listar_clases ()
        i = 1
        for clase in clases:
            print ("Creando clase", i)
            i+=1
            profesor = self.conseguir_profesor_con_disponibilidad (clase)
            if profesor != None:
                print ("Clase", i, "tiene asignado al profesor id", profesor.id)
                profesor_clase = ProfesorDictaClase(
                    id_profesor = profesor.id,
                    id_clase = clase.id
                )
                self.db.session.add(profesor_clase)

        self.db.session.commit()
