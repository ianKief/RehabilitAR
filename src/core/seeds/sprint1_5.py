from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

from src.core.usuarios import Cliente, EstadoUsuario, AptoFisico, EstadoAptoFisico
from src.core.reservas.reservas import Comentario
from src.core.pagos import Beneficio, TipoBeneficio, Pago, EstadoPago, ConceptoPago

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

#Épica 5: pagos
class SeedPagosSprint1 ():
    def __init__(self, db):
        self.db = db

    def run(self):
        print("🌱 Poblando datos para la épica Pagos (Sprint 1.5)...")
        try:
            # Si ya existen estos usuarios, no hacemos nada para que sea idempotente
            if self.db.session.query(Cliente).filter_by(email="clientecondescuento1@gmail.com").first():
                print("💡 Datos de Pagos (Sprint 1.5) ya existentes, no se realizaron cambios.")
                return

            cliente_con_descuento_acumulado = Cliente(
                nombre="Cliente con descuento",
                apellido="Pagos",
                dni="50000001",
                email="clientecondescuento1@gmail.com",
                password="123456",
                estado = EstadoUsuario.ACTIVO
            )
            self.db.session.add(cliente_con_descuento_acumulado)

            cliente_con_abono_terminado = Cliente(
                nombre="Cliente sin abono (desde hace poco)",
                apellido="Pagos",
                dni="50000002",
                email="clientecondescuento2@gmail.com",
                password="123456",
                estado = EstadoUsuario.ACTIVO
            )
            self.db.session.add(cliente_con_abono_terminado)

            self.db.session.flush()

            cliente_con_abono_muerto = Cliente(
                nombre="Cliente sin abono mucho",
                apellido="Pagos",
                dni="50000003",
                email="clientecondescuento3@gmail.com",
                password="123456",
                estado = EstadoUsuario.ACTIVO
            )
            self.db.session.add(cliente_con_abono_muerto)

            self.db.session.flush()

            pago_vencido = Pago (
                id_cliente = cliente_con_abono_terminado.id,
                payment_id = "lol",
                monto_total = 500,
                estado_pago = EstadoPago.COMPLETADO,
                concepto_pago = ConceptoPago.ABONO,
                fecha_creacion = datetime.now() - timedelta(days=40) # Creado hace 40 días, ya venció
            )
            self.db.session.add(pago_vencido)

            pago_muerto = Pago (
                id_cliente = cliente_con_abono_muerto.id,
                payment_id = "lolol",
                monto_total = 500,
                estado_pago = EstadoPago.COMPLETADO,
                concepto_pago = ConceptoPago.ABONO,
                fecha_creacion = datetime.now() - timedelta(days=90) # Creado hace 90 días, está suspendido
            )
            self.db.session.add(pago_muerto)
        
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

            self.db.session.commit()
            print("✅ Datos de Pagos (Sprint 1.5) poblados con éxito.")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error al poblar datos de Pagos (Sprint 1.5): {e}")
