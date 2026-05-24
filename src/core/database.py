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
    from src.core.usuarios import Usuario
    """Reinicia la base de datos eliminando todas las tablas y volviéndolas a crear."""
    print("Reiniciando la base de datos...")
    Base.metadata.drop_all(bind=db.engine)
    Base.metadata.create_all(bind=db.engine)
    print("Base de datos reiniciada.")

def seed_db():
    """Pobla la base de datos con datos de prueba."""
    from src.core.seeds.salas_seeds import SalaSeeder
    from src.core.seeds.usuarios_seeds import UsuarioSeeder
    from src.core.usuarios.usuarios import Usuario, RolUsuario, EstadoUsuario
    from src.core.database import db

    admin_existente = db.session.query(Usuario).filter_by(email='pruebasrehabilitar@gmail.com').first()
    if not admin_existente:
        admin = Usuario(
            nombre = "Admin",
            apellido = "Admin",
            dni = "12345678",
            email = "pruebasrehabilitar@gmail.com",
            password = "123456",
            rol = RolUsuario.ADMINISTRADOR,
            estado = EstadoUsuario.ACTIVO
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin creado con exito")
        
    seeder = SalaSeeder(db)
    seeder.run()
    usuario_seeder = UsuarioSeeder(db)
    usuario_seeder.run()