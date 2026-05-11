from flask import Flask
from flask import render_template
from src.web.controllers.presente_manual import presente_bp
from src.web.controllers.index_profesor import profesor_bp
from src.web.controllers.dev import dev_bp

def create_app(env="development", static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)
    app.secret_key = "dev"
    app.register_blueprint (profesor_bp)
    app.register_blueprint(presente_bp)
    app.register_blueprint(dev_bp)
    # ¿Alguno sabe cómo segmentar o hacer más pequeño lo de arriba? At: Alfonso
    @app.route("/")
    def home():
        return render_template("index.html")
    return app