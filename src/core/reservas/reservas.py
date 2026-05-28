from src.core.database import Base
from sqlalchemy import DateTime, String, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    id_cliente: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    id_clase: Mapped[int] = mapped_column(ForeignKey("clases.id"), nullable=False)

    # Relaciones
    cliente: Mapped["Cliente"] = relationship(back_populates="reservas")
    clase: Mapped["Clase"] = relationship(back_populates="reservas")
    comentarios: Mapped[list["Comentario"]] = relationship(back_populates="reserva", cascade="all, delete-orphan")
    cancelaciones: Mapped[list["Cancelacion"]] = relationship(back_populates="reserva", cascade="all, delete-orphan")

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
    id_reserva: Mapped[int] = mapped_column(ForeignKey("reserva.id"), nullable=False)
    
    # Relaciones
    reserva: Mapped["Reserva"] = relationship(back_populates="comentarios")

    # Campos de auditoría
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

class Cancelacion(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_reserva: Mapped[int] = mapped_column(ForeignKey("reserva"))

    descripcion: Mapped[str] = mapped_column(String(255), nullable=True)
    acredito_devolucion_previamente: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False)
    # La variable de arriba dice 

    # Relaciones:
    reserva: Mapped["Reserva"] = relationship(back_populates="cancelaciones")


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

class Cola(Base):
    __tablename__ = "colas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_clase: Mapped[int] = mapped_column(ForeignKey("clases.id"), nullable=False)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)

    cancelada: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    en_reserva: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)

    # Relaciones
    clase: Mapped[list["Clase"]] = relationship(back_populates="colas")
    cliente: Mapped[list["Cliente"]] = relationship(back_populates="colas")


    # Campos de auditoria
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

    fecha_modificacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        onupdate=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )