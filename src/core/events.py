# --- EVENTO 1: Creación automática al insertar un Usuario (Seeds e Imports incluidos) ---
from sqlalchemy import event
from src.core.usuarios import Usuario, Cliente, Profesor, Administrador
from src.core.usuarios.usuarios import Recepcionista
from src.core.notificaciones.notificaciones import ConfiguracionNotificacion, TipoNotificacion

CONFIG_POR_CLASE = {
    Cliente: [TipoNotificacion.OTRO, TipoNotificacion.ROL_MODIFICADO, TipoNotificacion.ESTADO_BLOQUEO, TipoNotificacion.CLASE_SUSPENDIDA, TipoNotificacion.ENTRADA_A_CLASE_DESDE_COLA, TipoNotificacion.VENCIMIENTO_APTO_FISICO, TipoNotificacion.ESTADO_APTO_FISICO, TipoNotificacion.FALTA_DE_PAGO, TipoNotificacion.PAGOS, TipoNotificacion.NUEVO_BENEFICIO],
    Administrador: [TipoNotificacion.OTRO, TipoNotificacion.ROL_MODIFICADO, TipoNotificacion.ESTADO_BLOQUEO, TipoNotificacion.CLASE_COLAPSADA, TipoNotificacion.NUEVA_CLASE_SUGERIDA, TipoNotificacion.NUEVA_APELACION_A_CLASE],
    Profesor: [TipoNotificacion.OTRO, TipoNotificacion.ROL_MODIFICADO, TipoNotificacion.ESTADO_BLOQUEO, TipoNotificacion.CLASE_SUSPENDIDA, TipoNotificacion.ESTADO_CLASE_APELADA, TipoNotificacion.ESTADO_POSTULACION_CLASE],
    Recepcionista: [TipoNotificacion.OTRO, TipoNotificacion.ROL_MODIFICADO, TipoNotificacion.ESTADO_BLOQUEO]
}

def crear_configuraciones_notificacion(_mapper, connection, target):
    """
    Se ejecuta automáticamente después de que un usuario es insertado en la BD.
    Utiliza la tabla directamente ('connection') para evitar bucles de sesión.
    """
    clase_actual = target.__class__
    tipos_permitidos = CONFIG_POR_CLASE.get(clase_actual, [])

    for tipo in tipos_permitidos:
        connection.execute(
            ConfiguracionNotificacion.__table__.insert().values(
                id_usuario=target.id,
                tipo=tipo,
                activado=True,
                habilitado=True
            )
        )

def init_events():
    event.listen(Usuario, 'after_insert', crear_configuraciones_notificacion, propagate=True)