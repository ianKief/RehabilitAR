from src.core.database import Base
from sqlalchemy import Boolean, DateTime, String, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from zoneinfo import ZoneInfo

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class Reserva(Base):
    __tablename__= "reserva"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asiste: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
