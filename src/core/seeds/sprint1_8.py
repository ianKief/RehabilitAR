from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.core.usuarios import Usuario, Profesor, Cliente, EstadoUsuario
from src.core.reservas.reservas import Reserva, Comentario, AsistenciaReserva
from src.core.clases import Clase, ProfesorDictaClase
from src.core.salas.salas import Sala

from src.core.functions import filtro_clase_actual

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

#Épica 8: asistencia y seguimiento
class SeedAsistenciaYSeguimientoSprint1 ():
    def __init__(self, db):
        self.db = db

    # 3 profesores

    def run(self):

        print("🌱 Poblando datos para la épica Asistencia y Seguimiento (Sprint 1.8)...")
        try:
            # Si ya existen estos usuarios, no hacemos nada para que sea idempotente
            if self.db.session.query(Profesor).filter_by(email="profesorays1@gmail.com").first():
                print("💡 Datos de Asistencia y Seguimiento (Sprint 1.8) ya existentes, no se realizaron cambios.")
                return

            # Hacemos cuenta de profesor 1
            profesor1 = Profesor(
                nombre="Profesor 1",
                apellido="AYS",
                dni="8000001", 
                email="profesorays1@gmail.com",
                password="123456",
                estado = EstadoUsuario.ACTIVO
            )
            self.db.session.add(profesor1)

            # Hacemos cuenta de profesor 2
            profesor2 = Profesor(
                nombre="Profesor 2",
                apellido="AYS",
                dni="8000002",
                email="profesorays2@gmail.com",
                password="123456",
                estado = EstadoUsuario.ACTIVO
            )
            self.db.session.add(profesor2)

            # Hacemos cuenta de profesor 3
            profesor3 = Profesor(
                nombre="Profesor 3",
                apellido="AYS",
                dni="8000003",
                email="profesorays3@gmail.com",
                password="123456",
                estado = EstadoUsuario.ACTIVO
            )
            self.db.session.add(profesor3)

            sala_sprint1_1 = Sala(
                numero_puerta="101-S1",
                descripcion="Sala Sprint 1 (Capacidad 4)",
                capacidad=4,
                estado="HABILITADA"
            )
            sala_sprint1_2 = Sala(
                numero_puerta="102-S1",
                descripcion="Sala Sprint 1 (Capacidad 1)",
                capacidad=1,
                estado="HABILITADA"
            )
            self.db.session.add(sala_sprint1_1)
            self.db.session.add(sala_sprint1_2)
            self.db.session.flush()

            clase1 = Clase(
                nombre= "Clase 1 de profesor 1 con reservas",
                especialidad= "Programación",
                duracion=180,
                descripcion = "Otorgamos una clase de 3 horas para 4 personas para que nuestro cliente pueda apreciar la implementación de la HU sin inconvenientes",
                fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date(),
                horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
                aprobada = True,
                tipo = "individual",
                sala_id = sala_sprint1_1.id
            )
            self.db.session.add(clase1)

            clase2 = Clase(
                nombre= "Clase 2 de profesor 2 sin reservas",
                especialidad= "Programación",
                duracion=180,
                descripcion = "Otorgamos una clase de 3 horas para 4 personas para que nuestro cliente pueda apreciar la implementación de la HU sin inconvenientes",
                fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date(),
                horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
                aprobada = True,
                tipo = "individual",
                sala_id = sala_sprint1_2.id
            )
            self.db.session.add(clase2)

            self.db.session.flush()

            profesor_dicta_clase1 = ProfesorDictaClase (
                id_profesor = profesor1.id,
                id_clase = clase1.id
            )
            self.db.session.add(profesor_dicta_clase1)

            profesor_dicta_clase2 = ProfesorDictaClase (
                id_profesor = profesor2.id,
                id_clase = clase2.id
            )
            self.db.session.add(profesor_dicta_clase2)

            query = (self.db.session.query(Cliente)
                .join(Reserva)
                .join(Clase)
                .filter(*filtro_clase_actual())
            )

            clientes_con_clase_actual = self.db.session.scalars(query).all()

            clientes = self.db.session.query(Cliente).filter(Cliente.id.notin_(clientes_con_clase_actual)).all()

            # Acá carga los datos de la clase vieja
            clase_vieja = Clase(
                nombre= "Clase 0 de profesor 1 con reservas",
                especialidad= "Programación",
                duracion=180,
                descripcion = "Esta clase ya sucedió hace un par de días",
                fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date() - timedelta(days=2),
                horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
                aprobada = True,
                tipo = "individual",
                sala_id = sala_sprint1_1.id
            )

            self.db.session.add (clase_vieja)
            self.db.session.flush()
            profesor_dicta_clase_viejo = ProfesorDictaClase (
                id_profesor = profesor1.id,
                id_clase = clase_vieja.id
            )
            self.db.session.add(profesor_dicta_clase_viejo)

            i = 0
            for cliente in clientes:
                nueva_reserva = Reserva (
                    id_cliente = cliente.id,
                    id_clase = clase_vieja.id,
                    asiste = AsistenciaReserva.PRESENTE
                )
                self.db.session.add(nueva_reserva)
                if i == 1:
                    self.db.session.flush()
                    nuevo_comentario = Comentario (
                        comentario = "Este es un comentario viejo",
                        reserva = nueva_reserva
                    )
                    self.db.session.add(nuevo_comentario)
                i+=1
                if (i == 3):
                    break

            # Acá a los clientes de la clase actual
            i = 0
            reservas = []
            for cliente in clientes:
                nueva_reserva = Reserva(
                    id_cliente = cliente.id,
                    id_clase = clase1.id
                )
                reservas.append(nueva_reserva)
                self.db.session.add(nueva_reserva)
                i+=1
                if (i == 4):
                    break
            
            self.db.session.flush()

            comentario1 = Comentario (
                comentario = "Este es el primer comentario para el cliente 2. Ojo que hay otro por ahí abajo...",
                id_reserva = reservas[1].id
            )
            self.db.session.add(comentario1)
            
            comentario2 = Comentario (
                comentario = "Esto significa que una reserva puede tener más de un comentario, por si llega a ser necesario...",
                id_reserva = reservas[1].id
            )
            self.db.session.add(comentario2)

            comentario3 = Comentario (
                comentario = "Llegó tarde",
                id_reserva = reservas[3].id
            )
            self.db.session.add(comentario3)

            # Del sprint 2: alguien con la clase cancelada :P

            cliente_cancelada = Cliente(
                nombre="cancelado",
                apellido="ays",
                dni="80000004",
                password="123456",
                estado = EstadoUsuario.ACTIVO,
                email="clienteclasecanceladaays@gmail.com"
            )
            self.db.session.add(cliente_cancelada)
            self.db.session.flush()

            reserva = Reserva(
                cliente = cliente_cancelada,
                clase = clase1,
                asiste = AsistenciaReserva.CANCELADA
            )
            self.db.session.add(reserva)

            self.db.session.commit()
            print("✅ Datos de Asistencia y Seguimiento (Sprint 1.8) poblados con éxito.")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error al poblar datos de Asistencia y Seguimiento (Sprint 1.8): {e}")