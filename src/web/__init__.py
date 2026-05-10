from flask import Flask
from flask import render_template
from src.web.controllers.auth import auth_bp

def create_app(env="development", static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)
    app.register_blueprint(auth_bp)
    @app.route("/")
    def home():
        return render_template("index.html")
    return app