from zoneinfo import ZoneInfo
from datetime import datetime

from src.core.usuarios import Cliente, EstadoUsuario, AptoFisico, EstadoAptoFisico
from src.core.reservas.reservas import Comentario
from src.core.pagos import Beneficio, TipoBeneficio

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

#Épica 5: pagos
class SeedPagosSprint1 ():
    def __init__(self, db):
        self.db = db

    def run(self):

        print ("Creando datos para la épica Pagos (5)")

        cliente_con_descuento_acumulado = Cliente(
            nombre="Cliente con descuento",
            apellido="Pagos",
            dni="50000001",
            email="clientecondescuento1@gmail.com",
            password="123456",
            estado = EstadoUsuario.ACTIVO
        )
        self.db.session.add(cliente_con_descuento_acumulado)

        self.db.session.flush()

        descuento = Beneficio (
            id_cliente = cliente_con_descuento_acumulado.id,
            tipo = TipoBeneficio.DESCUENTO,
            descripcion = "Super descuento del 45% totalmente irreal",
            porcentaje_descuento = 0.45
        )
        self.db.session.add(descuento)

        credito = Beneficio (
            id_cliente = cliente_con_descuento_acumulado.id,
            tipo = TipoBeneficio.CREDITO,
            descripcion = "Super credito",
        )
        self.db.session.add(credito)

        apto_fisico = AptoFisico (
            id_cliente = cliente_con_descuento_acumulado.id,
            estado = EstadoAptoFisico.ACEPTADO,
            fecha_carga = datetime.now(tz_arg).replace(tzinfo=None),
        )
        self.db.session.add(apto_fisico)

        print ("Enlazando descuento al cliente con descuento")

        self.db.session.commit()