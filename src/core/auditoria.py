from datetime import datetime
from flask import session
import enum
from src.core.database import Base, db
from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from sqlalchemy import Integer, String, DateTime, Enum, JSON, ForeignKey, select, desc

class TipoAccion(enum.Enum):
    # Seguridad y Autenticación
    LOGIN_EXITOSO = "LOGIN_EXITOSO"
    LOGIN_FALLIDO = "LOGIN_FALLIDO"
    LOGOUT = "LOGOUT"
    REGISTRO_USUARIO = "REGISTRO_USUARIO"
    CAMBIO_CONTRASENA = "CAMBIO_CONTRASENA"
    
    # Gestión de Usuarios (por Admin)
    CREACION_USUARIO_ADMIN = "CREACION_USUARIO_ADMIN"
    CAMBIO_ROL = "CAMBIO_ROL"
    BLOQUEO_USUARIO = "BLOQUEO_USUARIO"
    HABILITACION_USUARIO = "HABILITACION_USUARIO"
    ELIMINACION_USUARIO = "ELIMINACION_USUARIO"
    APROBACION_APTO = "APROBACION_APTO"
    RECHAZO_APTO = "RECHAZO_APTO"
    
    # Gestión de Salas
    CREACION_SALA = "CREACION_SALA"
    MODIFICACION_SALA = "MODIFICACION_SALA"
    ELIMINACION_SALA = "ELIMINACION_SALA"
    CAMBIO_ESTADO_SALA = "CAMBIO_ESTADO_SALA"

    # Gestión de Clases
    CREACION_CLASE = "CREACION_CLASE"
    RESOLUCION_POSTULACION = "RESOLUCION_POSTULACION"
    
    # Operaciones Financieras
    ACTUALIZACION_PRECIO = "ACTUALIZACION_PRECIO"
    PAGO_REGISTRADO = "PAGO_REGISTRADO"
    WEBHOOK_MP_RECIBIDO = "WEBHOOK_MP_RECIBIDO"
    PAGO_SEÑA = "PAGO_SEÑA"
    
    # Operaciones del Sistema
    FINALIZACION_CLASE = "FINALIZACION_CLASE"
    BLOQUEO_USUARIO_INASISTENCIA = "BLOQUEO_USUARIO_INASISTENCIA" #TODO

class LogAuditoria(Base):
    __tablename__ = 'logs_auditoria'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    tipo_accion: Mapped[TipoAccion] = mapped_column(Enum(TipoAccion), nullable=False)
    id_usuario_actor: Mapped[int] = mapped_column(Integer, ForeignKey('usuarios.id'), nullable=True)
    rol_usuario_actor: Mapped[str] = mapped_column(String(50), nullable=True)
    id_entidad_objetivo: Mapped[int] = mapped_column(Integer, nullable=True)
    detalles: Mapped[dict] = mapped_column(JSON, nullable=True)
    

    usuario_actor = relationship('Usuario', foreign_keys=[id_usuario_actor])

def registrar_log(tipo_accion, id_entidad_objetivo=None, detalles=None):
    """Función helper para registrar un evento de auditoría."""
    log = LogAuditoria(
        tipo_accion=tipo_accion,
        id_usuario_actor=session.get('usuario_id'),
        rol_usuario_actor=session.get('rol'),
        id_entidad_objetivo=id_entidad_objetivo,
        detalles=detalles
    )
    db.session.add(log)
    db.session.commit()

def listar_logs(**kwargs):
    """
    Obtiene una lista de logs de auditoría con filtros opcionales.
    """
    query = select(LogAuditoria).options(joinedload(LogAuditoria.usuario_actor)).order_by(desc(LogAuditoria.timestamp))

    # Filtros
    tipo_accion_str = kwargs.get('tipo_accion')
    if tipo_accion_str:
        try:
            tipo_accion_enum = TipoAccion[tipo_accion_str]
            query = query.filter(LogAuditoria.tipo_accion == tipo_accion_enum)
        except KeyError:
            # Si el tipo de acción no es válido, no se aplica el filtro
            pass

    id_usuario_actor = kwargs.get('id_usuario_actor')
    if id_usuario_actor:
        query = query.filter(LogAuditoria.id_usuario_actor == id_usuario_actor)

    fecha_desde = kwargs.get('fecha_desde')
    if fecha_desde:
        query = query.filter(LogAuditoria.timestamp >= fecha_desde)

    fecha_hasta = kwargs.get('fecha_hasta')
    if fecha_hasta:
        from datetime import timedelta
        query = query.filter(LogAuditoria.timestamp < fecha_hasta + timedelta(days=1))

    logs = db.session.execute(query).scalars().all()
    
    return logs