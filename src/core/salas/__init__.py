from sqlalchemy import select
from src.core.database import db
from src.core.salas.salas import Sala

def listar_salas():
    stmt = select(Sala).order_by(Sala.numero_puerta)
    return db.session.execute(stmt).scalars().all()