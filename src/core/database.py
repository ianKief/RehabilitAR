from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

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
    from src.core.notificaciones.notificaciones import Notificacion
    from src.core.usuarios import Usuario
    from src.core.reservas.reservas import Reserva, Comentario, Cola, Cancelacion
    from src.core.pagos.pagos import Pago, DetallePago, Beneficio, PrecioClase
    from src.core import events
    
    """Reinicia la base de datos eliminando todas las tablas y volviéndolas a crear."""
    print("Reiniciando la base de datos...")
    with db.engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()
    Base.metadata.create_all(bind=db.engine)
    print("Base de datos reiniciada.")

def seed_db():
    """Pobla la base de datos con datos de prueba."""
    from src.core.database import db

    from src.core.seeds.salas_seeds import SalaSeeder
    #from src.core.seeds.profesores_seeds import ProfesorSeeder
    #from src.core.seeds.postulacionSeeder import PostulacionSeeder
    #from src.core.seeds.clases_seeds2 import ClaseSeeder2
    from src.core.seeds.clases_seeds import ClaseSeeder, ProfesorDictaClaseSeeder
    from src.core.seeds.especialidades_seeds import EspecialidadSeeder
    from src.core.seeds.usuarios_seeds import UsuarioSeeder
    from src.core.seeds.sprint1_5 import SeedPagosSprint1
    from src.core.seeds.sprint1_8 import SeedAsistenciaYSeguimientoSprint1
    from src.core.seeds.sprint1_9 import SeedListaDeEspera
    from src.core.seeds.notificaciones_seeds import NotificacionesSeeder
    from src.core.seeds.estadistiticas_seed import EstadisticasSeeder
    from src.core import events

    # Definimos el orden lógico de ejecución de los seeders
    seeders = [
        SalaSeeder(db),
        EspecialidadSeeder(db),
        UsuarioSeeder(db),
        #ProfesorSeeder(db),
        ClaseSeeder(db),
        #PostulacionSeeder(db),
        ProfesorDictaClaseSeeder(db),
        SeedPagosSprint1(db),
        SeedAsistenciaYSeguimientoSprint1(db),
        SeedListaDeEspera (db),
        NotificacionesSeeder (db),
        EstadisticasSeeder(db)
    ]

    for seeder in seeders:
        seeder.run()
        
    print("¡Base de datos poblada exitosamente!")

def seed_db_admin():
    """
    Pobla la base de datos con unicamente un admin de prueba.
    """
    from src.core.database import db
    from src.core.seeds.usuarios_seeds import AdminSeeder

    admin_seeder = AdminSeeder(db)
    admin_seeder.run()
