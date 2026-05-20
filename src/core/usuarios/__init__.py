from sqlalchemy import select
from src.core.database import db
from src.core.usuarios.usuarios import Usuario

def listar_usuarios():
    """Devuelve una lista con todos los usuarios registrados."""
    stmt = select(Usuario).order_by(Usuario.id)
    return db.session.execute(stmt).scalars().all()

def crear_usuario(**kwargs):
    """Crea un nuevo usuario en la base de datos."""
    nuevo_usuario = Usuario(**kwargs)
    db.session.add(nuevo_usuario)
    db.session.commit()
    return nuevo_usuario