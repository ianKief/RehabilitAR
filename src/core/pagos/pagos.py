from src.core.database import Base
from sqlalchemy import Integer, String, DateTime, Enum, Float, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List
import enum

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

# Clases de pago

class ConceptoPago (enum.Enum):
    RESERVA = "reserva" # Vale tanto para reservar como para esperar en la cola
    ABONO = "abono"

class EstadoPago (enum.Enum):
    PENDIENTE = "pendiente"
    COMPLETADO = "completado"

class Pago (Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    
    # id del pago que devuelve mercado pago
    payment_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    monto_total: Mapped[int] = mapped_column(Integer, nullable=False)
    estado_pago: Mapped[EstadoPago] = mapped_column(Enum(EstadoPago), default=EstadoPago.PENDIENTE, nullable=False)
    concepto_pago: Mapped[ConceptoPago] = mapped_column(Enum(ConceptoPago), default=ConceptoPago.RESERVA, nullable=False)

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

    # Relationships

    detalle_pago = relationship("DetallePago", back_populates="pago")
    beneficios = relationship("Beneficio", back_populates="pago")
    abono = relationship("Abono", back_populates="pago")


class DetallePago (Base):
    __tablename__ = "detalle_pago"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_pago: Mapped[int] = mapped_column(ForeignKey("pagos.id"))

    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships

    pago = relationship("Pago", back_populates="detalle_pago")
    detalle_pago_reserva = relationship("DetallePagoReserva", back_populates="detalle_pago")

class Abono(Base):
    __tablename__ = "abonos"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_pago: Mapped[int] = mapped_column( ForeignKey("pagos.id"),nullable=False)

    dia_fijo: Mapped[int] = mapped_column(Integer, nullable=False)
    #TODO convertir en enum
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime,nullable=False, default=datetime.now(tz_arg).replace(tzinfo=None))
    fecha_fin: Mapped[datetime] = mapped_column(DateTime,nullable=False)

    # Relationships:
    pago = relationship("Pago", back_populates="abono")





# Tablas de conexión de Pago y Clase (para ambas categorías)

class DetallePagoReserva (Base):
    __tablename__ ="pago_clase"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_detalle_pago: Mapped[int] = mapped_column(ForeignKey("detalle_pago.id"))
    id_reserva: Mapped[int] = mapped_column(ForeignKey("reserva.id"))

    # Relationships:

    detalle_pago = relationship("DetallePago", back_populates="detalle_pago_reserva")



#Beneficio

class TipoBeneficio(enum.Enum):
    CREDITO = "credito"
    DESCUENTO = "descuento"

class Beneficio (Base):
    __tablename__ ="beneficios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_pago: Mapped[int] = mapped_column(ForeignKey("pagos.id"),nullable=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    tipo: Mapped[TipoBeneficio] = mapped_column(Enum(TipoBeneficio), default=TipoBeneficio.CREDITO, nullable=False)
    fecha_vencimiento: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=True)
    porcentaje_descuento: Mapped[Float] = mapped_column(Float, nullable=True)
    usado: Mapped[Boolean] = mapped_column(Boolean, nullable=True, default=False)
    # Porcentaje_descuento va de 0 a 1

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

    pago = relationship("Pago", back_populates="beneficios")

    """NOTA: No se agrega fecha_modificación porque hay una sola razón por la que podría cambiar: se usó en un pago.
    En ese caso, notar que la fecha de modificación es exactamente el momento del pago, cosa que se puede rastrear
    accediendo a id_pago y llegando a pago.fecha_creacion"""



class PrecioClase(Base):
    __tablename__ = "precio_clase"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    precio: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )
    fecha_hasta: Mapped[datetime] = mapped_column (DateTime, default=None, nullable=True)
    # No lo testeé
