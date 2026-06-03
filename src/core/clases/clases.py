from src.core.reservas.reservas import Cola, Reserva
from src.core.salas.salas import Sala

from src.core.database import Base
from sqlalchemy import Boolean, Date, DateTime, String, Integer, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime, time
from zoneinfo import ZoneInfo
from src.core.salas.salas import Sala

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class Clase(Base):
    __tablename__ = "clases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    especialidad: Mapped[str] = mapped_column(String(20), nullable=False)
    duracion: Mapped[int] = mapped_column(Integer, nullable=False) # duracion en minutos
    descripcion: Mapped[str] = mapped_column(String(255), nullable=True)
    suspendida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    fecha_clase: Mapped[date] = mapped_column(Date, nullable=False)
    horario: Mapped[time] = mapped_column(Time, nullable=False)
    aprobada:Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    sala_id: Mapped[int] = mapped_column(ForeignKey("salas.id"), nullable=False)
    # RELACIÓN: Esto te permite hacer "clase.sala.capacidad_maxima" o "clase.sala.numero_puerta" directo en Python
    aviso_alta_demanda:Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)

    # Relaciones
    sala: Mapped["Sala"] = relationship("Sala")
    reservas: Mapped[list["Reserva"]] = relationship(back_populates="clase", cascade="all, delete-orphan")
    colas: Mapped[list["Cola"]] = relationship(back_populates="clase", cascade="all, delete-orphan")

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

    @property
    def capacidad_maxima(self) -> int:
        """Propiedad dinámica para retrocompatibilidad con las vistas (Jinja)"""
        return self.sala.capacidad if self.sala else 0


    def __repr__(self):
        return (f"<ClaseRehabilitacion(id={self.id}, nombre='{self.nombre}', "
                f"especialidad='{self.especialidad}', fecha='{self.fecha_clase}', "
                f"horario='{self.horario}', suspendida={self.suspendida})>")

class ProfesorDictaClase (Base):
    __tablename__ = "profesor_clase"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_profesor: Mapped[int] = mapped_column(Integer, nullable=False)
    id_clase: Mapped[int] = mapped_column(Integer, nullable=False)

    # Campos de auditoría
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None),
        nullable=False
    )

class PostulacionClase(Base):
    __tablename__ = "postulacion_clase"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clase_id: Mapped[int] = mapped_column(ForeignKey("clases.id"), nullable=False)
    profesor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones para moverte fácil en Python
    clase = relationship("Clase")
    profesor = relationship("Usuario")

    from sqlalchemy import ForeignKey

class ClaseBloque(Base):
    __tablename__ = "clases_bloques"

    # id_bloque forma parte de la PK compuesta. Es un entero asignado lógicamente por vos.
    id_bloque: Mapped[int] = mapped_column(primary_key=True)
    
    # id_clase es la otra parte de la PK compuesta y además es la Foreign Key con borrado en cascada físico.
    id_clase: Mapped[int] = mapped_column(
        ForeignKey("clases.id", ondelete="CASCADE"), 
        primary_key=True
    )

    # Opcional: Relación bidireccional estilo 2.0 (por si la necesitan para navegar el objeto)
    # Reemplazá "Clase" por el nombre exacto de tu clase del modelo de clases.
    clase: Mapped["Clase"] = relationship(backref="bloque_asociado")
