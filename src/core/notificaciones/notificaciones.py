from src.core.database import Base
from sqlalchemy import Boolean, DateTime, String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from zoneinfo import ZoneInfo
import enum

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class TipoNotificacion (enum.Enum):
    # Tipos generales

    # Tipos del administrador

    # Tipos del cliente

    # Tipos del profesor
    TIPO1 = "tipo1"
    # Ingrese acá sus tipos

class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo: Mapped[TipoNotificacion] = mapped_column(Enum(TipoNotificacion), default=TipoNotificacion.TIPO1, nullable=False)
    contenido: Mapped[String] = mapped_column(String(200), default="", nullable=False)
    leido: Mapped[Boolean] = mapped_column(Boolean, default=False, nullable=True) # No recomendaría manipular este campo
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)

    
    # Relaciones
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="notificaciones")

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

