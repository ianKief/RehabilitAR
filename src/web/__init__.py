import os
from flask import Flask, request,render_template
from flask_mail import Mail
from src.web.config import config
from src.web.handlers import error
from src.core.database import init_db, reset_db, seed_db

"""
Las importaciones de src.web.controllers deben hacerse dentro de create_app() para evitar problemas de importación circular. 
"""

mail = Mail()
def create_app():
    app = Flask(__name__, static_folder="static")

    # Cargar configuración
    app.config.from_object(config)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
    
    # Inicializar base de datos
    init_db(app)

    # Inicializar extensión de correo
    mail.init_app(app)

    # Registrar blueprints
    from src.web.controllers.salas import bp as salas_bp
    from src.web.controllers.auth import auth_bp
    from src.web.controllers.usuarios import users_bp as usuarios_bp

    app.register_blueprint(salas_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)

    # Registrar CLI commands
    @app.cli.command("reset-db")
    def reset_db_command():
        # Reinicia la base de datos eliminando todas las tablas y volviéndolas a crear.
        reset_db()

    @app.cli.command("seed-db")
    def seed_db_command():
        """Pobla la base de datos con datos de prueba."""
        seed_db()

    # Registrar manejadores de errores
    app.register_error_handler(404, error.not_found)
    app.register_error_handler(401, error.unauthorized)
    app.register_error_handler(403, error.forbidden)
    app.register_error_handler(500, error.internal_server_error)

    @app.route("/")
    def home():
        return render_template("home.html", current_path=request.path)

    return app