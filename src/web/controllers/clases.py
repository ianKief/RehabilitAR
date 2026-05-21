from flask import Blueprint, abort, render_template, request
from src.core.clases import listar_clases, obtener_clase_por_id, obtener_postulantes_clase

bp = Blueprint("clases", __name__, url_prefix="/clases")

@bp.get("/admin")
def listar_clases_admin():
    """Ruta que muestra el listado de clases para el administrador."""
    clases_registradas = listar_clases()
    return render_template("clases/clases_creadas.html", clases=clases_registradas, current_path=request.path)

@bp.get("/admin/<int:clase_id>")
def ver_detalle_admin(clase_id):
    """Ruta que delega la búsqueda al core y renderiza el detalle de la clase."""
    
    # 1. Le pedimos al core que busque la clase
    clase = obtener_clase_por_id(clase_id)
    
    # 2. El controlador maneja el error de cara al cliente web (HTTP 404)
    if not clase:
        return abort(404, description="La clase de rehabilitación no existe.")
    
    # 3. Le pedimos al core los profesores postulados para esa clase
    postulantes = obtener_postulantes_clase(clase_id)
    
    # 4. Renderizamos la vista enviando los datos limpios
    return render_template(
        "clases/clase_detalle.html", 
        clase=clase, 
        postulantes=postulantes,
        current_path=request.path
    )