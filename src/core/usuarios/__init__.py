from sqlalchemy import select
from src.core.database import db
from src.core.usuarios.usuarios import Usuario

def listar_usuarios():
    """Devuelve una lista con todos los usuarios registrados."""
    stmt = select(Usuario).order_by(Usuario.id)
    return db.session.execute(stmt).scalars().all()

def crear_usuario(**kwargs):
    """Crea un nuevo usuario en la base de datos."""
    stmt = select(Usuario).filter_by(email=kwargs.get('email'))
    usuario_existente = db.session.execute(stmt).scalar_one_or_none()

    if usuario_existente:
        raise ValueError("El correo electrónico ya está registrado.")
    
    nuevo_usuario = Usuario(**kwargs)
    db.session.add(nuevo_usuario)
    db.session.commit()
    return nuevo_usuario