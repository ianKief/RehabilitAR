from src.core.database import Base
from sqlalchemy import Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from zoneinfo import ZoneInfo
import enum

class EstadoSala(enum.Enum):
    HABILITADA = "habilitada"
    DESHABILITADA = "deshabilitada"

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class Sala(Base):
    __tablename__ = "salas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numero_puerta: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=True)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[EstadoSala] = mapped_column(Enum(EstadoSala), default=EstadoSala.HABILITADA, nullable=False)
    eliminada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )
    fecha_modificacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        onupdate=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

    def __repr__(self):
        return f"<Sala(id={self.id}, numero_puerta='{self.numero_puerta}', capacidad={self.capacidad}, estado='{self.estado}')>"
    
