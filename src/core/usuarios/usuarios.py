from src.core.database import Base
from sqlalchemy import Integer, String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from zoneinfo import ZoneInfo
import enum

class EstadoUsuario(enum.Enum):
    PENDIENTE = "pendiente"
    ACTIVO = "activo"
    BLOQUEADO = "bloqueado"

class RolUsuario(enum.Enum):
    CLIENTE = "cliente"
    RECEPCIONISTA = "recepcionista"
    PROFESOR = "profesor"
    ADMINISTRADOR = "administrador"

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class EstadoAptoFisico(enum.Enum):
    SIN_CARGAR = "SIN_CARGAR"
    EN_REVISION = "EN_REVISION"
    ACEPTADO = "ACEPTADO"
    RECHAZADO = "RECHAZADO"

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=True)
    dni: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str] = mapped_column(String(20), nullable=True)
    fecha_nacimiento: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ruta_apto_fisico: Mapped[str] = mapped_column(String(255), nullable=True)
    estado_apto_fisico: Mapped[EstadoAptoFisico] = mapped_column(Enum(EstadoAptoFisico), default=EstadoAptoFisico.SIN_CARGAR, nullable=True)
    
    rol: Mapped[RolUsuario] = mapped_column(Enum(RolUsuario), default=RolUsuario.CLIENTE, nullable=False)
    estado: Mapped[EstadoUsuario] = mapped_column(Enum(EstadoUsuario), default=EstadoUsuario.PENDIENTE, nullable=True)

    codigo_verificacion : Mapped[str] = mapped_column(String(6), nullable=True)
    codigo_verificacion_expira : Mapped[datetime] = mapped_column(DateTime, nullable=True)
    intentos_codigo: Mapped[int] = mapped_column(Integer, default=0, nullable=True)

    intentos_login: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    bloqueado_hasta: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
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
        return f"<Usuario(id={self.id}, nombre='{self.nombre}', email='{self.email}', rol='{self.rol.value}', estado='{self.estado.value}')>"