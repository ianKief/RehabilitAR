from flask import Blueprint

from src.web.controllers.profesor.presente_manual import registrar_asistencia_manual
from src.web.controllers.profesor.index_profesor import renderizar_index_profesor

profesor_bp = Blueprint('profesor', __name__, url_prefix="/profesor")

@profesor_bp.route('/', methods=['GET'])
def index_profesor ():
    return renderizar_index_profesor()

@profesor_bp.route('/presente_manual', methods=['GET', 'POST'])
def presente_manual ():
    return registrar_asistencia_manual()