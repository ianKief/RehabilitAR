from zoneinfo import ZoneInfo

from src.core.usuarios import Cliente, EstadoUsuario
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
            password="contraseña",
            estado = EstadoUsuario.ACTIVO
        )
        self.db.session.add(cliente_con_descuento_acumulado)

        print ("ID del cliente con descuento AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:", cliente_con_descuento_acumulado)
        self.db.session.flush()

        beneficio = Beneficio (
            id_cliente = cliente_con_descuento_acumulado.id,
            tipo = TipoBeneficio.DESCUENTO,
            descripcion = "Super descuento del 45% totalmente irreal",
            porcentaje_descuento = 0.45
        )
        self.db.session.add(beneficio)

        print ("Enlazando descuento al cliente con descuento")

        self.db.session.commit()