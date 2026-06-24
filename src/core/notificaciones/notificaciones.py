from src.core.database import Base
from sqlalchemy import Boolean, DateTime, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from zoneinfo import ZoneInfo
import enum

tz_arg = ZoneInfo("America/Argentina/Buenos_Aires")

class TipoNotificacion (enum.Enum):
    # Tipos generales
    OTRO = "otro" # Para uso aleatorio - valor default
    ROL_MODIFICADO = "rol_modificado"
    ESTADO_BLOQUEO = "estado_bloqueo" # Bloqueo o desbloqueo de usuario
    CLASE_SUSPENDIDA = "clase_suspendida" # avisa a profesor y a cliente
    
    # Tipos del administrador
    CLASE_COLAPSADA = "clase_colapsada"
    NUEVA_CLASE_SUGERIDA = "nueva_clase_sugerida"

    # Tipos del cliente
    ENTRADA_A_CLASE_DESDE_COLA = "entrada_a_clase_desde_cola"
    VENCIMIENTO_APTO_FISICO = "vencimiento_apto_fisico"
    ESTADO_APTO_FISICO = "estado_apto_fisico" # Rechazado o aceptado
    FALTA_DE_PAGO = "falta_de_pago" # Se envía los 10 del mes
    PAGO_REALIZADO = "pago_realizado" # aplica para los abonos y para las clases en sí
    NUEVO_BENEFICIO = "nuevo_beneficio"

    # Tipos del profesor
    ESTADO_CLASE_APELADA = "estado_clase_apelada" # Aceptado o rechazado
    ESTADO_POSTULACION_CLASE = "estado_postulacion_clase" # Aceptado o rechazado
    # Ingrese acá sus tipos

class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo: Mapped[TipoNotificacion] = mapped_column(Enum(TipoNotificacion), default=TipoNotificacion.OTRO, nullable=True)
    titulo: Mapped[String] = mapped_column(String(30), nullable=False)
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

    __table_args__ = (
        UniqueConstraint('id_usuario', 'tipo', name='uq_usuario_tipo_notificacion'),
    )

class ConfiguracionNotificacion(Base):
    __tablename__ = "configuracion_notificaciones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tipo: Mapped[TipoNotificacion] = mapped_column(Enum(TipoNotificacion), default=TipoNotificacion.OTRO, nullable=False)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    habilitado: Mapped[Boolean] = mapped_column(Boolean, default=True, nullable=True) # No recomendaría manipular este campo
    activado: Mapped[Boolean] = mapped_column(Boolean, default=True, nullable=True)
    # Habilitado vs activado: dado que un usuario puede cambiar de rol, habilitado supone un borrado lógico de los tipos de notificaciones, dado que queremos recaudar información y no se recomienda hacer borrado físico. Activado, por otro lado, es el switch de si recibe notificaciones o no.

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="configuracion_notificaciones")
