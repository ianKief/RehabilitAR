from flask import Blueprint, render_template, request
from src.core.clases import listar_clases

bp = Blueprint("clases", __name__, url_prefix="/clases")

@bp.get("/admin")
def listar_clases_admin():
    """Ruta que muestra el listado de clases para el administrador."""
    clases_registradas = listar_clases()
    return render_template("clases/clases_creadas.html", clases=clases_registradas, current_path=request.path)