from sqlalchemy import select
from src.core.database import db
from src.core.usuarios.usuarios import Usuario, RolUsuario, EstadoUsuario


def obtener_usuario_por_id_core(user_id):
    """Devuelve un usuario dado su ID."""
    return db.session.get(Usuario, user_id)

def listar_usuarios(nombre=None, apellido=None, dni=None, email=None, rol=None, estado=None):
    """Devuelve una lista con todos los usuarios registrados.
    Si hay parametros, los filtra."""
    stmt = select(Usuario).order_by(Usuario.id)
    if nombre:
        stmt = stmt.where(Usuario.nombre == nombre)
    if apellido:
        stmt = stmt.where(Usuario.apellido == apellido)
    if dni:
        stmt = stmt.where(Usuario.dni == dni)
    if email:
        stmt = stmt.where(Usuario.email == email)
    if rol:
        stmt = stmt.where(Usuario.rol == RolUsuario(rol))
    if estado:
        stmt = stmt.where(Usuario.estado == EstadoUsuario(estado))
        
    return db.session.execute(stmt).scalars().all()

def crear_usuario(**kwargs):
    """Crea un nuevo usuario en la base de datos."""
    stmt = select(Usuario).filter_by(email=kwargs.get('email'))
    usuario_existente = db.session.execute(stmt).scalar_one_or_none()

    if usuario_existente:
        raise ValueError("El correo electrónico ya está registrado.")
    
    rol_str = kwargs.pop('rol')
    nuevo_usuario = Usuario(**kwargs, rol=RolUsuario(rol_str))
    db.session.add(nuevo_usuario)
    db.session.commit()
    return nuevo_usuario