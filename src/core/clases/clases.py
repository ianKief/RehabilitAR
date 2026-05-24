from src.core.salas.salas import Sala
from src.core.database import Base
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class Clase(Base):
    __tablename__ = "clases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    especialidad: Mapped[str] = mapped_column(String(20), nullable=False)
    duracion: Mapped[int] = mapped_column(Integer, nullable=False) # duracion en minutos
    capacidad_maxima: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(255), nullable=True)
    suspendida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_clase: Mapped[date] = mapped_column(Date, nullable=False)
    horario: Mapped[time] = mapped_column(Time, nullable=False)
    aprobada:Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    sala_id: Mapped[int] = mapped_column(ForeignKey("salas.id"), nullable=False)
    # RELACIÓN: Esto te permite hacer "clase.sala.capacidad_maxima" o "clase.sala.numero_puerta" directo en Python
    sala: Mapped["Sala"] = relationship("Sala")

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


    def __repr__(self):
        return (f"<ClaseRehabilitacion(id={self.id}, nombre='{self.nombre}', "
                f"especialidad='{self.especialidad}', fecha='{self.fecha_clase}', "
                f"horario='{self.horario}', suspendida={self.suspendida})>")