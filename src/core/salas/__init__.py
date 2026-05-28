from sqlalchemy import select
from src.core.database import db
from src.core.salas.salas import EstadoSala, Sala

def listar_salas():
    stmt = select(Sala).order_by(Sala.numero_puerta)
    return db.session.execute(stmt).scalars().all()

def obtener_sala(id):
    """Obtiene una sala por su ID."""
    return db.session.get(Sala, id)

def listar_salas_habilitadas():
    """Retorna los objetos completos de las salas habilitadas (para sacar ID y Puerta en el HTML)."""
    query = select(Sala).filter(Sala.estado == EstadoSala.HABILITADA)
    return db.session.scalars(query).all()