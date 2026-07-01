import os
from flask import Flask, request,render_template,session, request
from flask_mail import Mail
from src.web.config import config
from src.core.database import init_db, reset_db, seed_db, seed_db_admin
import mercadopago
from src.web.handlers import error
from src.core.pagos import estado_abono_usuario
from src.core.events import init_events

"""
Las importaciones de src.web.controllers deben hacerse dentro de create_app() para evitar problemas de importación circular. 
"""

mail = Mail()
def create_app():
    app = Flask(__name__, static_folder="static")
    app.mp_sdk = mercadopago.SDK(os.environ.get("MP_ACCESS_TOKEN"))

    # Cargar configuración
    app.config.from_object(config)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    # Configuración de la cookie de sesión para que funcione con Ngrok
    ngrok_url = os.environ.get("URL_NGROK")
    if ngrok_url and "ngrok" in ngrok_url:
        # Extrae solo el hostname, ej: "1a2b-3c4d.ngrok.io"
        app.config['SERVER_NAME'] = ngrok_url.split('//')[1]

    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

    db = init_db(app)
    
    # Inicializar extensión de correo
    mail.init_app(app)

    # Registrar blueprints
    from src.web.controllers.salas import bp as salas_bp
    from src.web.controllers.auth import auth_bp
    from src.web.controllers.usuarios import users_bp as usuarios_bp
    from src.web.controllers.clases import bp as clases_bp # hago el import acá porque creo que puede generarse un bucle de imports si se coloca al inicio
    from src.web.controllers.profesor.routes_profesor import profesor_bp
    from src.web.controllers.reservas import reservas_bp
    from src.web.controllers.pagos import bp as pagos_bp
    from src.web.controllers.profesor.asistencia import asistencia_bp
    from src.web.controllers.notificaciones import bp as notificaciones_bp

    app.register_blueprint(salas_bp)
    app.register_blueprint(profesor_bp)
    app.register_blueprint(clases_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(pagos_bp)
    app.register_blueprint(asistencia_bp)
    app.register_blueprint(notificaciones_bp)

    # Registrar CLI commands
    @app.cli.command("reset-db")
    def reset_db_command():
        # Reinicia la base de datos eliminando todas las tablas y volviéndolas a crear.
        reset_db()

    @app.cli.command("seed-db")
    def seed_db_command():
        """Pobla la base de datos con datos de prueba."""
        seed_db()

    @app.cli.command("seed-db-admin")
    def seed_db_admin_command():
        """Pobla la base de datos con unicamente un admin de prueba."""
        seed_db_admin()

    with app.app_context():
        init_events(db)

    @app.context_processor
    def notificaciones():
        from src.core.notificaciones import obtener_notificaciones_del_usuario, contar_notificaciones_no_leidas
        current_user_id = session.get('usuario_id')
        if current_user_id != None:
            notificaciones = obtener_notificaciones_del_usuario(current_user_id)
            unread_count = contar_notificaciones_no_leidas(current_user_id)
            
            return dict(
                notificaciones=notificaciones,
                unread_count=unread_count
            )
        
        return dict(notificaciones=[], unread_count=0)

    # Registrar manejadores de errores
    app.register_error_handler(404, error.not_found)
    app.register_error_handler(401, error.unauthorized)
    app.register_error_handler(403, error.forbidden)
    app.register_error_handler(500, error.internal_server_error)

    @app.route("/")
    def home():
        user_id = session.get("usuario_id")
        estado = estado_abono_usuario(user_id)
        rol = session.get("rol")
        if isinstance(rol, str):
            rol = rol.lower()
        return render_template("home.html", current_path=request.path,estado_abono=estado,rol=rol)

    return app