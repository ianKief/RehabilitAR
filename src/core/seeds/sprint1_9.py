from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random

from src.core.usuarios import Cliente, Profesor, ProfesorDictaClase, EstadoUsuario, RolUsuario, EstadoUsuario
from src.core.usuarios.usuarios import AptoFisico, EstadoAptoFisico
from src.core.clases import Clase
from src.core.reservas import Reserva, Cola
from src.core.salas import Sala
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

        cliente_apto_fisico_viejo = Cliente (
            nombre="Apto Viejo",
            apellido="Casi Vence",
            dni="90000002",
            email="clienteespera1@gmail.com",
            password="123456",
            estado = EstadoUsuario.ACTIVO
        )
        self.db.session.add(cliente_apto_fisico_viejo)

        self.db.session.flush()

        apto_fisico = AptoFisico (
            cliente = cliente_apto_fisico_viejo,
            ruta_archivo = "",
            estado = EstadoAptoFisico.ACEPTADO,
            fecha_carga = datetime.now(tz_arg).replace(tzinfo=None).date() - timedelta(days=364),
            # O sea, para dentro de dos días venció
            comentario = "Apto físico :P"
        )
        self.db.session.add(apto_fisico)
        print("Usuarios creados. Creando clases y reservas")

        aula_re_llena = Sala (
            numero_puerta = "epica9",
            capacidad = 1
        )
        self.db.session.add(aula_re_llena)

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
            tipo = "individual"
        )
        self.db.session.add(clase_re_llena)

        self.db.session.flush()

        profesor_dicta_clase = ProfesorDictaClase (
            id_profesor = profesor.id,
            id_clase = clase_re_llena.id
        )
        self.db.session.add(profesor_dicta_clase)

        reserva = Reserva (
            id_cliente = 2,
            id_clase = clase_re_llena.id
        )
        self.db.session.add(reserva)

        print ("Generando clientes nuevos por si anteriores generados no son suficientes")

        for i in range(10):
            nombre = f"Usuario 10{i}"
            apellido = f"Apellido 10{i}"
            dni = f"{random.randint(10000000, 99999999)}"
            email = f"user10{i}@gmail.com"
            password = f"password{i}"
            rol = RolUsuario.CLIENTE
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
            )

            usuario = Cliente(**datos_usuario)
                
            self.db.session.add(usuario)

        print ("Agregando gente en la lista de espera")

        query = (self.db.session.query(Cliente)
            .filter(Cliente.id > 3)
        )
        clientes = self.db.session.scalars(query).all()

        i = 0
        for cliente in clientes:
            nueva_cola = Cola (
                id_cliente = cliente.id,
                id_clase = clase_re_llena.id
            )
            self.db.session.add(nueva_cola)
            i+=1
            if (i == 9):
                break
        if (i != 9):
            print ("Error: no se pudieron poner 9 clientes en la clase llena. Por favor ingrese más clientes o repita el seed ")
        
        self.db.session.commit()