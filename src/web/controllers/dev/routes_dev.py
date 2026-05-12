from flask import Blueprint

from src.web.controllers.dev.alterar_sesion import alterar_sesion_manual

dev_bp = Blueprint('dev', __name__, url_prefix="/dev")

@dev_bp.route('/alterar_sesion', methods=['GET', 'POST'])
def alterar_sesion ():
    return alterar_sesion_manual ()