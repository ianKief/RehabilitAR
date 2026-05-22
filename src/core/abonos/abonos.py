from src.core.database import Base
from sqlalchemy import Integer, String, DateTime, Enum, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from zoneinfo import ZoneInfo
import enum

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

# Clases de pago

class Pago (Base):
    __tablename__ = "pago"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(Integer, nullable=False)
    monto: Mapped[int] = mapped_column(Integer, nullable=False) # Puede ser Float, pero dado la economía no me pareció necesario xd

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

class Mensualidad (Base):
    __tablename__ ="mensualidad"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_pago: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    """NOTA: fecha_inicio NO es necesariamente el momento del registro del pago.
    Ejemplo: pago la mensualidad para una clase del jueves. Pago el lunes. La fecha es el jueves.
    Para acceder a datos de auditoría del pago, fijarse fecha_creación de Pago"""



# Tablas de conexión de Pago y Clase (para ambas categorías)

class PagoClase(Base):
    __tablename__ ="pago_clase"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_clase: Mapped[int] = mapped_column(Integer, nullable=False)
    id_pago: Mapped[int] = mapped_column(Integer, nullable=False)

class MensualidadClaseFija(Base):
    __tablename__ ="pago_clase_fija"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_mensualidad: Mapped[int] = mapped_column(Integer, nullable=False)
    id_clase_fija: Mapped[int] = mapped_column(Integer, nullable=False)



#Beneficio

class TipoBeneficio(enum.Enum):
    CREDITO = "credito"
    DESCUENTO = "descuento"

class Beneficio (Base):
    __tablename__ ="beneficio"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_pago: Mapped[int] = mapped_column(Integer, nullable=True)
    tipo: Mapped[TipoBeneficio] = mapped_column(Enum(TipoBeneficio), default=TipoBeneficio.CREDITO, nullable=False)
    fecha_vencimiento: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=True)
    porcentaje_descuento: Mapped[Float] = mapped_column(Float, nullable=True)

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

    """NOTA: No se agrega fecha_modificación porque hay una sola razón por la que podría cambiar: se usó en un pago.
    En ese caso, notar que la fecha de modificación es exactamente el momento del pago, cosa que se puede rastrear
    accediendo a id_pago y llegando a pago.fecha_creacion"""