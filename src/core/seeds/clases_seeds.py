import random
from datetime import date, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import aliased

from src.core.clases import Clase, listar_clases  # El import de tu modelo de clases
from src.core.usuarios import Usuario, ProfesorDictaClase
from src.core.salas.salas import Sala
from src.core.usuarios.usuarios import RolUsuario

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

        # Optimizamos consultas: traemos solo los IDs en lugar de cargar todos los objetos pesados a la memoria
        ids_salas = list(self.db.session.scalars(select(Sala.id).filter_by(eliminada=False)))
        ids_profesores = list(self.db.session.scalars(select(Usuario.id).filter_by(rol=RolUsuario.PROFESOR)))

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
                especialidad = random.choice(self.especialidades)
                nombre = random.choice(self.nombres_por_especialidad[especialidad])
                horario = horarios_del_dia[i]
                duracion = random.choice([45, 60, 90])
                id_sala_asignada = random.choice(ids_salas) if ids_salas else None
                
                # Asignamos el profesor fuera del bucle de semanas para que la clase Fija mantenga siempre al mismo profesor y sala.
                id_profesor_asignado = random.choice(ids_profesores) if ids_profesores else None

                for semana in range(4):
                    fecha_clase = fecha_base + timedelta(weeks=semana)
                    clase = Clase(
                        nombre=nombre,
                        especialidad=especialidad,
                        duracion=duracion,
                        descripcion=f"Sesión enfocada en {especialidad.lower()}. Trabajo de movilidad y fuerza progresiva. Tipo: Fija.",
                        suspendida=False,
                        fecha_clase=fecha_clase,
                        horario=horario,
                        aprobada=True,
                        tipo="Fija",
                        id_sala=id_sala_asignada
                    )
                    self.db.session.add(clase)
                    clases_y_profesores.append((clase, id_profesor_asignado, "Fija"))

            # 2 Clases Individuales por semana (horarios distintos a las fijas de ese día)
            for semana in range(4):
                fecha_clase = fecha_base + timedelta(weeks=semana)
                for i in range(2, 4):
                    especialidad = random.choice(self.especialidades)
                    nombre = random.choice(self.nombres_por_especialidad[especialidad])
                    horario = horarios_del_dia[i]
                    duracion = random.choice([45, 60, 90])
                    id_sala_asignada = random.choice(ids_salas) if ids_salas else None
                    
                    id_profesor_asignado = random.choice(ids_profesores) if ids_profesores else None
                    clase = Clase(
                        nombre=nombre,
                        especialidad=especialidad,
                        duracion=duracion,
                        descripcion=f"Sesión enfocada en {especialidad.lower()}. Trabajo de movilidad y fuerza progresiva. Tipo: Individual.",
                        suspendida=False,
                        fecha_clase=fecha_clase,
                        horario=horario,
                        aprobada=True,
                        tipo="Individual",
                        id_sala=id_sala_asignada
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
            print(f"Creada: {clase.nombre} | {clase.fecha_clase} {clase.horario} | {tipo} | Sala: {clase.id_sala} | Prof: {id_profesor}")

        self.db.session.commit()
        print("¡Se han guardado las clases correctamente!")


class ProfesorDictaClaseSeeder ():
    """NOTA: según las HU #90 y #91, se considera especialidad a las 3 de arriba."""
    def __init__(self, db):
        self.db = db
    
    def run (self):
        # La asignación de profesores ahora se maneja directamente en ClaseSeeder.
        # Esto garantiza que las clases fijas mantengan al mismo profesor en todas sus repeticiones,
        # y simplifica enormemente la lógica de disponibilidad sin generar fallos en la base de datos.
        pass