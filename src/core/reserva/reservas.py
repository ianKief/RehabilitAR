from src.core.database import Base
from sqlalchemy import Boolean, DateTime, String, Integer, Enum 
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from zoneinfo import ZoneInfo
import enum

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class AsistenciaReserva(enum.Enum):
    AUSENTE = "ausente"
    PRESENTE = "presente"
    CANCELADA = "cancelada"

class Reserva(Base):
    __tablename__= "reserva"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asiste: Mapped[AsistenciaReserva] = mapped_column(Enum(AsistenciaReserva), default=AsistenciaReserva.AUSENTE, nullable=True)
    id_cliente: Mapped[int] = mapped_column(Integer, nullable=False)
    id_clase: Mapped[int] = mapped_column(Integer, nullable=False)

    # Campos de auditoría
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )
    fecha_modificacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        onupdate=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

class Comentario(Base):
    __tablename__ = "comentario"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comentario: Mapped[str] = mapped_column(String(255), nullable=False)
    id_reserva: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Campos de auditoría
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )
