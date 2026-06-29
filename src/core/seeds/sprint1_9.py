from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random

from src.core.usuarios import Cliente, Profesor, ProfesorDictaClase, EstadoUsuario, RolUsuario, EstadoUsuario
from src.core.usuarios.usuarios import AptoFisico, EstadoAptoFisico
from src.core.clases import Clase
from src.core.reservas import Reserva, Cola
from src.core.salas import Sala
from src.core.pagos import Pago, Abono, EstadoPago, ConceptoPago
tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class SeedListaDeEspera ():
    def __init__(self, db):
        self.db = db

    def run(self):

        print ("Creando datos para la épica de Cola de espera (9)")

        profesor = Profesor(
            nombre="Profesor De",
            apellido="Clase Llena",
            dni="90000001", 
            email="profesorespera@gmail.com",
            password="123456",
            estado = EstadoUsuario.ACTIVO
        )
        self.db.session.add(profesor)

        cliente = Cliente (
            nombre="Cliente con abono",
            apellido="De cola de espera",
            dni="90000002",
            email="clienteespera1@gmail.com",
            password="123456",
            estado = EstadoUsuario.ACTIVO
        )
        self.db.session.add(cliente)
        self.db.session.flush()

        pago = Pago (
            id_cliente = cliente.id,
            payment_id = "hoigadhogaho1738y191yfheo4f2972h49f2pf",
            monto_total = 500,
            estado_pago = EstadoPago.COMPLETADO,
            concepto_pago = ConceptoPago.ABONO
        )
        self.db.session.add(pago)

        apto_fisico = AptoFisico (
            cliente = cliente,
            ruta_archivo = "",
            estado = EstadoAptoFisico.ACEPTADO,
            fecha_carga = datetime.now(tz_arg).replace(tzinfo=None).date(),
            comentario = "Apto físico :P"
        )
        self.db.session.add(apto_fisico)
        
        self.db.session.flush()

        abono = Abono (
            pago = pago,
            dia_fijo = 1, # este es martes??
            fecha_inicio = datetime.now(tz_arg).replace(tzinfo=None).date(),
            fecha_fin = datetime.now(tz_arg).replace(tzinfo=None).date() + timedelta(days=30)
        )
        self.db.session.add(abono)
    
        cliente_apto_fisico_viejo = Cliente (
            nombre="Apto Viejo",
            apellido="Casi Vence",
            dni="90000003",
            email="clienteespera2@gmail.com",
            password="123456",
            estado = EstadoUsuario.ACTIVO
        )
        self.db.session.add(cliente_apto_fisico_viejo)

        profesor2 = Profesor(
            nombre="Profesor2 De",
            apellido="Clase Llena",
            dni="90000004", 
            email="profesorespera2@gmail.com",
            password="123456",
            estado = EstadoUsuario.ACTIVO
        )
        self.db.session.add(profesor2)
        self.db.session.flush()

        apto_fisico_viejo = AptoFisico (
            cliente = cliente_apto_fisico_viejo,
            ruta_archivo = "",
            estado = EstadoAptoFisico.ACEPTADO,
            fecha_carga = datetime.now(tz_arg).replace(tzinfo=None) - timedelta(days=362),
            # O sea, para dentro de dos días venció
            comentario = "Apto físico :P"
        )
        self.db.session.add(apto_fisico_viejo)
        print("Usuarios creados. Creando clases y reservas")

        aula_re_llena = Sala (
            numero_puerta = "epica9",
            capacidad = 1
        )

        otra_aula = Sala (
            numero_puerta = "epica9_2",
            capacidad = 1
        )
        self.db.session.add(aula_re_llena)
        self.db.session.add(otra_aula)

        self.db.session.flush()

        clase_re_llena = Clase(
            nombre= "Clase con 9 esperas",
            especialidad= "Programación",
            duracion=180,
            sala = aula_re_llena,
            descripcion = "Otorgamos una clase de 3 horas para 1 persona y 9 esperando para que nuestro cliente pueda ver el mail enviado al administrativo",
            fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date() + timedelta(days=2),
            horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
            aprobada = True,
            tipo = "Individual"
        )
        self.db.session.add(clase_re_llena)

        # Esto lo agrego porque si hago el test en jueves y viernes no puedo comprobar la condición luego :P
        clase_re_llena2 = Clase(
            nombre= "Clase con 9 esperas segunda edición",
            especialidad= "Programación",
            duracion=180,
            sala = aula_re_llena,
            descripcion = "Otorgamos una clase de 3 horas para 1 persona y 9 esperando para que nuestro cliente pueda ver el mail enviado al administrativo",
            fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date() + timedelta(days=4),
            horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
            aprobada = True,
            tipo = "Individual"
        )
        self.db.session.add(clase_re_llena2)

        clase_que_se_da_cuando_otra_1 = Clase(
            nombre= "Clase asíncrona 1",
            especialidad= "Programación",
            duracion=180,
            sala = aula_re_llena,
            descripcion = "Otorgamos una clase de 3 horas que se da cuando otra clase, para ver qué onda",
            fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date() + timedelta(days=1),
            horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
            aprobada = True,
            tipo = "Individual"
        )
        self.db.session.add(clase_que_se_da_cuando_otra_1)
        clase_que_se_da_cuando_otra_2 = Clase(
            nombre= "Clase asíncrona 2",
            especialidad= "Programación",
            duracion=180,
            sala = otra_aula,
            descripcion = "Otorgamos otra clase de 3 horas que se da cuando otra clase, para ver qué onda",
            fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date() + timedelta(days=1),
            horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
            aprobada = True,
            tipo = "Individual"
        )
        self.db.session.add(clase_que_se_da_cuando_otra_2)
        self.db.session.flush()

        # Estas son otras dos clases por si las 2 anteriores caen en feriado
        clase_que_se_da_cuando_otra_1_2 = Clase(
            nombre= "Clase asíncrona 1",
            especialidad= "Programación",
            duracion=180,
            sala = aula_re_llena,
            descripcion = "Otorgamos una clase de 3 horas que se da cuando otra clase, para ver qué onda",
            fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date() + timedelta(days=4),
            horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
            aprobada = True,
            tipo = "Individual"
        )
        self.db.session.add(clase_que_se_da_cuando_otra_1_2)
        clase_que_se_da_cuando_otra_2_2 = Clase(
            nombre= "Clase asíncrona 2",
            especialidad= "Programación",
            duracion=180,
            sala = otra_aula,
            descripcion = "Otorgamos otra clase de 3 horas que se da cuando otra clase, para ver qué onda",
            fecha_clase = datetime.now(tz_arg).replace(tzinfo=None).date() + timedelta(days=4),
            horario = datetime.now(tz_arg).replace(tzinfo=None).time(),
            aprobada = True,
            tipo = "Individual"
        )
        self.db.session.add(clase_que_se_da_cuando_otra_2_2)
        self.db.session.flush()


        profesor_dicta_clase3 = ProfesorDictaClase (
            id_profesor = profesor.id,
            id_clase = clase_que_se_da_cuando_otra_1.id
        )
        self.db.session.add(profesor_dicta_clase3)

        profesor_dicta_clase4 = ProfesorDictaClase (
            id_profesor = profesor2.id,
            id_clase = clase_que_se_da_cuando_otra_2.id
        )
        self.db.session.add(profesor_dicta_clase4)
        
        profesor_dicta_clase5 = ProfesorDictaClase (
            id_profesor = profesor.id,
            id_clase = clase_que_se_da_cuando_otra_1_2.id
        )
        self.db.session.add(profesor_dicta_clase5)
        
        profesor_dicta_clase6 = ProfesorDictaClase (
            id_profesor = profesor2.id,
            id_clase = clase_que_se_da_cuando_otra_1_2.id
        )
        self.db.session.add(profesor_dicta_clase6)

        profesor_dicta_clase = ProfesorDictaClase (
            id_profesor = profesor.id,
            id_clase = clase_re_llena.id
        )
        self.db.session.add(profesor_dicta_clase)

        profesor_dicta_clase2 = ProfesorDictaClase (
            id_profesor = profesor.id,
            id_clase = clase_re_llena2.id
        )
        self.db.session.add(profesor_dicta_clase2)

        reserva = Reserva (
            id_cliente = 2,
            id_clase = clase_re_llena.id
        )
        self.db.session.add(reserva)

        reserva2 = Reserva (
            id_cliente = 2,
            id_clase = clase_re_llena2.id
        )
        self.db.session.add(reserva2)

        print ("Generando clientes nuevos para anotar en las colas")

        for i in range(9):
            nombre = f"Usuario 10{i}"
            apellido = f"Apellido 10{i}"
            dni = f"{random.randint(10000000, 99999999)}"
            email = f"user10{i}@gmail.com"
            password = f"password{i}"
            estado = EstadoUsuario.ACTIVO
            direccion = f"Direccion {i}"
            telefono = f"123456789{i}"
            fecha_nacimiento = datetime(1990, 1, (i % 28) + 1)
            
            datos_usuario = dict(
                nombre=nombre,
                apellido=apellido,
                dni=dni, 
                email=email, 
                password=password, 
                estado=estado, 
                direccion=direccion, 
                telefono=telefono,
                fecha_nacimiento = fecha_nacimiento
            )

            usuario = Cliente(**datos_usuario)
                
            self.db.session.add(usuario)
            self.db.session.flush()

            nueva_cola = Cola (
                id_cliente = usuario.id,
                id_clase = clase_re_llena.id
            )
            self.db.session.add(nueva_cola)
            nueva_cola2 = Cola (
                id_cliente = usuario.id,
                id_clase = clase_re_llena2.id
            )
            self.db.session.add(nueva_cola2)
        
        self.db.session.commit()