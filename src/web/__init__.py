from flask import Flask
from flask import render_template

def create_app(env="development", static_folder="../../static"):
    app = Flask(__name__, static_folder=static_folder)

    @app.route("/")
    def home():
        return render_template("index.html")
    
    from src.web.clases import clases_bp
    app.register_blueprint(clases_bp)
    
    return app