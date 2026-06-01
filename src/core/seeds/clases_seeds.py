import calendar
import random
from datetime import date, time, timedelta
from sqlalchemy import select
from src.core.salas.salas import Sala, EstadoSala  # Asegurá estas rutas
from src.core.clases.clases import Clase, ClaseBloque              # Asegurá esta ruta

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
            time(8, 0), time(10, 0), time(12, 0), 
            time(14, 0), time(16, 0), time(18, 0)
        ]

    def run(self):
        print("Insertando clases de prueba...")

        # 1. Traemos los OBJETOS completos de las salas habilitadas
        query_salas = select(Sala).filter(Sala.estado == EstadoSala.HABILITADA)
        salas_disponibles = self.db.session.scalars(query_salas).all()

        if not salas_disponibles:
            print("⚠️ Error: No se encontraron salas habilitadas en la BD. Ejecutá primero el seeder de salas.")
            return

        hoy = date.today()
        
        # 🔥 Contador para autogestionar identificadores únicos de bloques en el Seeder
        proximo_id_bloque = 1

        # Generamos 8 intenciones de clases distribuidas en la agenda
        for i in range(8):
            especialidad = random.choice(self.especialidades)
            nombre = random.choice(self.nombres_por_especialidad[especialidad])
            tipo = random.choice(self.tipos_clases)
            horario = random.choice(self.horarios_prueba)
            
            # Repartimos las fechas iniciales en un rango de 10 días
            dias_en_adelante = random.randint(1, 10)
            fecha_inicial = hoy + timedelta(days=dias_en_adelante)

            # Evitamos fin de semana para la fecha base
            if fecha_inicial.weekday() in [5, 6]:
                fecha_inicial += timedelta(days=2)

            sala_asignada = random.choice(salas_disponibles)

            # Validamos capacidad según el modelo de Sala
            if sala_asignada.capacidad > 1:
                capacidad_maxima = random.randint(2, sala_asignada.capacidad)
            else:
                capacidad_maxima = 1

            if tipo == 'Individual':
                capacidad_maxima = 1

            duracion = random.choice([45, 60])

            # 2. DETERMINAR LAS FECHAS DE IMPACTO
            fechas_a_crear = []
            
            # 🔥 Guardamos el ID que usará este bloque si la intención resulta ser Fija
            id_bloque_actual = None
            
            if tipo == "Fija":
                id_bloque_actual = proximo_id_bloque
                # Incrementamos para la próxima intención fija que pueda salir en el loop principal
                proximo_id_bloque += 1 
                
                anio = fecha_inicial.year
                mes = fecha_inicial.month
                dia_semana_objetivo = fecha_inicial.weekday()

                cal = calendar.monthcalendar(anio, mes)
                for semana in cal:
                    dia = semana[dia_semana_objetivo]
                    if dia != 0:
                        fecha_calculada = date(anio, mes, dia)
                        if fecha_calculada >= hoy:
                            fechas_a_crear.append(fecha_calculada)
            else:
                fechas_a_crear.append(fecha_inicial)

            # 3. PERSISTENCIA EN EL BUCLE DE RECURRENCIA
            for f in fechas_a_crear:
                clase = Clase(
                    nombre=nombre,
                    especialidad=especialidad,
                    duracion=duracion,
                    capacidad_maxima=capacidad_maxima,
                    descripcion=f"Clase de prueba ({tipo}). Enfoque: {especialidad.lower()}. Espacio controlado en Sala {sala_asignada.numero_puerta}.",
                    suspendida=False,
                    fecha_clase=f,
                    horario=horario,
                    aprobada=True,
                    tipo=tipo,
                    sala_id=sala_asignada.id
                )
                self.db.session.add(clase)
                
                # 🔥 SI ES FIJA: Hacemos el acoplamiento con la tabla intermedia
                if tipo == "Fija":
                    # Forzamos la asignación del ID de la clase en PostgreSQL sin cerrar la transacción
                    self.db.session.flush()
                    
                    asociacion_bloque = ClaseBloque(
                        id_bloque=id_bloque_actual,
                        id_clase=clase.id
                    )
                    self.db.session.add(asociacion_bloque)
                    print(f" -> Seeder: Preparada [Fija] {clase.nombre} (Bloque: {id_bloque_actual}) para el {clase.fecha_clase}")
                else:
                    print(f" -> Seeder: Preparada [Individual] {clase.nombre} para el {clase.fecha_clase}")

        # Confirmamos todos los bloques e intermedias juntos en Postgres
        try:
            self.db.session.commit()
            print("¡Se han guardado las clases y sus relaciones de bloque correctamente en PostgreSQL!")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error al ejecutar el commit del seeder: {e}")
