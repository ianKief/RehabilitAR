from flask import Flask, request,render_template
from src.web.config import config
from src.core.database import db, init_db, reset_db, seed_db

from src.web.handlers import error
from src.web.controllers.salas import bp as salas_bp
from src.web.controllers.profesor.routes_profesor import profesor_bp

def create_app():
    app = Flask(__name__, static_folder="static")

    # Cargar configuración
    app.config.from_object(config)

    # Inicializar base de datos
    init_db(app)


    # Registrar blueprints
    from src.web.controllers.clases import bp as clases_bp # hago el import acá porque creo que puede generarse un bucle de imports si se coloca al inicio
    
    app.register_blueprint(salas_bp)
    app.register_blueprint (profesor_bp)
    app.register_blueprint(clases_bp)
    
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