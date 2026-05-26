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
    from src.core.clases.clases import Clase
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
    # seeder de clases
    from src.core.seeds.clases_seeds import ClaseSeeder
    seeder_clases = ClaseSeeder(db)
    seeder_clases.run()

    # Seeder de Profesores y Especialidades
    # Levantamos las especialidades e IDs bases antes de procesar la cartelera
    from src.core.seeds.profesores_seeds import ProfesorSeeder
    seeder_profesores = ProfesorSeeder(db)
    seeder_profesores.run()

    from src.core.seeds.postulacionSeeder import PostulacionSeeder
    seeder_postulacion= PostulacionSeeder(db)
    seeder_postulacion.run()
    