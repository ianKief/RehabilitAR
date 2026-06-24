# --- EVENTO 1: Creación automática al insertar un Usuario (Seeds e Imports incluidos) ---
from sqlalchemy import event, insert
from src.core.usuarios import Usuario, Cliente, Profesor, Administrador
from src.core.notificaciones.notificaciones import ConfiguracionNotificacion, TipoNotificacion

CONFIG_POR_CLASE = {
    Cliente: [TipoNotificacion.OTRO, TipoNotificacion.ROL_MODIFICADO, TipoNotificacion.ESTADO_BLOQUEO, TipoNotificacion.CLASE_SUSPENDIDA, TipoNotificacion.ENTRADA_A_CLASE_DESDE_COLA, TipoNotificacion.VENCIMIENTO_APTO_FISICO, TipoNotificacion.ESTADO_APTO_FISICO, TipoNotificacion.FALTA_DE_PAGO, TipoNotificacion.PAGOS, TipoNotificacion.NUEVO_BENEFICIO],
    Administrador: [TipoNotificacion.OTRO, TipoNotificacion.ROL_MODIFICADO, TipoNotificacion.ESTADO_BLOQUEO, TipoNotificacion.CLASE_COLAPSADA, TipoNotificacion.NUEVA_CLASE_SUGERIDA],
    Profesor: [TipoNotificacion.OTRO, TipoNotificacion.ROL_MODIFICADO, TipoNotificacion.ESTADO_BLOQUEO, TipoNotificacion.CLASE_SUSPENDIDA, TipoNotificacion.ESTADO_CLASE_APELADA, TipoNotificacion.ESTADO_POSTULACION_CLASE]
}

def crear_configuraciones_notificacion(mapper, connection, target):
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

# --- EVENTO 2: Cambio de Rol (before_flush) ---
"""
def detectar_cambio_de_rol(session, flush_context, instances):
    for obj in session.dirty:
        if isinstance(obj, Usuario):
            state = event.inspect(obj) # db
            attr = state.attrs.get('rol')
            if attr and attr.history.has_changes():
                session.execute(
                    ConfiguracionNotificacion.__table__.update()
                    .where(ConfiguracionNotificacion.__table__.c.id_usuario == obj.id)
                    .values(habilitado=False)
                )
                nuevo_rol = attr.history.added[0]
                tipos_nuevos = CONFIG_POR_CLASE.get(nuevo_rol, [])
                for tipo in tipos_nuevos:
                    tabla_config = ConfiguracionNotificacion.__table__
                    
                    # Intentamos hacer la inserción base
                    stmt = insert(tabla_config).values(
                        id_usuario=obj.id,
                        tipo=tipo,
                        activado=True,
                        habilitado=True
                    )
                    
                    # Si hay conflicto en las columnas especificadas, actualiza en su lugar
                    upsert_stmt = stmt.on_conflict_do_update(
                        index_elements=['id_usuario', 'tipo'], # Nombre de las columnas de la restricción
                        set_=dict(habilitado=True, activado=True) # Campos a modificar si ya existe
                    )
                    
                    session.execute(upsert_stmt)
"""
def init_events(db):
    event.listen(Usuario, 'after_insert', crear_configuraciones_notificacion, propagate=True)
    
    # event.listen(db.session, 'before_flush', detectar_cambio_de_rol) ACTUALMENTE FUERA DE USO