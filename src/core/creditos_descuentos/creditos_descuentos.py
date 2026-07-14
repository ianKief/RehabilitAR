from src.core.database import Base

from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfo

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")
import enum

class TipoBeneficio(enum.Enum):
    CREDITO = "credito"
    DESCUENTO = "descuento"


class CreditoDescuento(Base):
    __tablename__ = "creditos_descuentos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    id_cliente: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clientes.id"),
        nullable=False
    )

    id_cancelacion: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cancelaciones.id"),
        nullable=True
    )

    tipo: Mapped[TipoBeneficio] = mapped_column(
        Enum(TipoBeneficio),
        nullable=False
    )

    cantidad: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    motivo: Mapped[str] = mapped_column(
        String(255),
        default="Clase cancelada"
    )

    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

    cliente: Mapped["Cliente"] = relationship()

    cancelacion: Mapped["Cancelacion"] = relationship()