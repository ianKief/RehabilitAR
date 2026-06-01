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
    from src.core.reservas.reservas import Reserva, Comentario
    from src.core.pagos.pagos import Pago, DetallePago,DetallePagoReserva,Beneficio,PrecioClase, Abono
    
    """Reinicia la base de datos eliminando todas las tablas y volviéndolas a crear."""
    print("Reiniciando la base de datos...")
    Base.metadata.drop_all(bind=db.engine)
    Base.metadata.create_all(bind=db.engine)
    print("Base de datos reiniciada.")

def seed_db():
    """Pobla la base de datos con datos de prueba."""
    from src.core.database import db
    from src.core.seeds.salas_seeds import SalaSeeder
    from src.core.seeds.clases_seeds import ClaseSeeder, ProfesorDictaClaseSeeder
    from src.core.seeds.usuarios_seeds import UsuarioSeeder
    from src.core.seeds.sprint1_escenarios import SeedAsistenciaYSeguimientoSprint1
    from src.core.seeds.lista_de_espera_sprint1_seeds import SeedListaDeEspera

    # Definimos el orden lógico de ejecución de los seeders
    seeders = [
        SalaSeeder(db),
        UsuarioSeeder(db),
        ClaseSeeder(db),
        ProfesorDictaClaseSeeder(db),
        SeedAsistenciaYSeguimientoSprint1(db),
        SeedListaDeEspera (db)
    ]

    for seeder in seeders:
        seeder.run()
        
    print("¡Base de datos poblada exitosamente!")