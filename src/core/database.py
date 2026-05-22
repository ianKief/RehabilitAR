from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

db = SQLAlchemy()

def init_db(app):
    """Inicializa la base de datos con la aplicación Flask."""
    db.init_app(app)
    return db

class Base(DeclarativeBase):
    """Devuelve la clase base para los modelos de SQLAlchemy."""
    pass

def reset_db():
    from src.core.salas import Sala
    from src.core.clases.clases import Clase, ProfesorDictaClase
    from src.core.usuarios import Usuario
    from src.core.reserva import Reserva, Comentario
    """Reinicia la base de datos eliminando todas las tablas y volviéndolas a crear."""
    print("Reiniciando la base de datos...")
    Base.metadata.drop_all(bind=db.engine)
    Base.metadata.create_all(bind=db.engine)
    print("Base de datos reiniciada.")

def seed_db():
    """Pobla la base de datos con datos de prueba."""

    from src.core.seeds.salas_seeds import SalaSeeder
    seeder = SalaSeeder(db) 
    seeder.run()

    from src.core.seeds.clases_seeds import ClaseSeeder, ProfesorDictaClaseSeeder
    seeder_clases = ClaseSeeder(db)
    seeder_clases.run()

    from src.core.seeds.usuarios_seeds import UsuarioSeeder
    usuario_seeder = UsuarioSeeder(db)
    usuario_seeder.run()

    seeder_profesor_clases = ProfesorDictaClaseSeeder(db)
    seeder_profesor_clases.run()

    from src.core.seeds.reserva_seeds import ReservaSeeder, ComentarioSeeder
    seeder_reserva = ReservaSeeder(db) 
    seeder_reserva.run()
    seeder_comentario = ComentarioSeeder (db)
    seeder_comentario.run()