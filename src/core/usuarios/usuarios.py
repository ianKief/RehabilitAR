from typing import List
from src.core.reservas.reservas import Cola, Reserva
from src.core.database import Base
from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, Boolean,Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
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

class AptoFisico(Base):
    __tablename__ = "aptos_fisicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"), unique=True)
    ruta_archivo: Mapped[str] = mapped_column(String(255), nullable=True)
    estado: Mapped[EstadoAptoFisico] = mapped_column(Enum(EstadoAptoFisico), default=EstadoAptoFisico.SIN_CARGAR)
    fecha_carga: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(tz_arg).replace(tzinfo=None), nullable=True)
    comentario: Mapped[str] = mapped_column(String(500), nullable=True)

    cliente: Mapped["Cliente"] = relationship(back_populates="apto_fisico")

class TipoEspecialidad(enum.Enum):
    SUPERIOR = "TREN SUPERIOR"
    MEDIO = "TREN MEDIO"
    INFERIOR = "TREN INFERIOR"

class Especialidad(Base):
    __tablename__ = "especialidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[TipoEspecialidad] = mapped_column(Enum(TipoEspecialidad), unique=True, nullable=False)
    profesores: Mapped[List["Profesor"]] = relationship(back_populates="especialidad")

# ==========================================
# 1. CLASE PADRE 
# ==========================================

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
    
    rol: Mapped[RolUsuario] = mapped_column(Enum(RolUsuario), default=RolUsuario.CLIENTE, nullable=False)
    estado: Mapped[EstadoUsuario] = mapped_column(Enum(EstadoUsuario), default=EstadoUsuario.PENDIENTE, nullable=True)

    codigo_verificacion : Mapped[str] = mapped_column(String(6), nullable=True)
    codigo_verificacion_expira : Mapped[datetime] = mapped_column(DateTime, nullable=True)
    intentos_codigo: Mapped[int] = mapped_column(Integer, default=0, nullable=True)

    intentos_login: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    bloqueado_hasta: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    notificaciones: Mapped[list["Notificacion"]] = relationship("Notificacion", back_populates="usuario")
    configuracion_notificaciones: Mapped[List["ConfiguracionNotificacion"]] = relationship("ConfiguracionNotificacion", back_populates="usuario", cascade="all, delete-orphan")

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
    
    __mapper_args__ = {
        "polymorphic_on": "rol",
        "polymorphic_identity": "usuario_base"
    }

# ==========================================
# 2. CLASES HIJAS
# ==========================================

class Cliente(Usuario):
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    fecha_ultima_verificacion: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relaciones
    apto_fisico: Mapped["AptoFisico"] = relationship(back_populates="cliente", uselist=False, cascade="all, delete-orphan")
    reservas: Mapped[List["Reserva"]] = relationship(back_populates="cliente", cascade="all, delete-orphan")
    colas: Mapped[list["Cola"]] = relationship(back_populates="cliente", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_identity": RolUsuario.CLIENTE
    }

class Profesor(Usuario):
    __tablename__ = "profesores"
    id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    id_especialidad: Mapped[int] = mapped_column(ForeignKey("especialidades.id"), nullable=True)

    # Relaciones
    especialidad: Mapped["Especialidad"] = relationship(back_populates="profesores")

    __mapper_args__ = {
        "polymorphic_identity": RolUsuario.PROFESOR
    }

class Recepcionista(Usuario):
    __tablename__ = "recepcionistas"
    id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": RolUsuario.RECEPCIONISTA
    }

class Administrador(Usuario):
    __tablename__ = "administradores"
    id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": RolUsuario.ADMINISTRADOR
    }