from flask import Blueprint

from src.web.controllers.profesor.presente_manual import registrar_asistencia_manual
from src.web.controllers.profesor.index_profesor import renderizar_index_profesor
from src.web.controllers.profesor.listado_alumnos import consultar_listado_alumnos
from src.web.controllers.profesor.perfil_alumno import cargar_perfil_alumno
from src.web.controllers.profesor.subir_comentario import subir_comentario_alumnoXclase


profesor_bp = Blueprint('profesor', __name__, url_prefix="/profesor")

@profesor_bp.route('/', methods=['GET'])
def index_profesor ():
    return renderizar_index_profesor()

@profesor_bp.route('/presente_manual', methods=['GET', 'POST'])
def presente_manual ():
    return registrar_asistencia_manual()

@profesor_bp.route('/listado_alumnos', methods=['GET'])
def listado_alumnos ():
    return consultar_listado_alumnos()

@profesor_bp.route('/perfil_alumno/<dni>', methods=['GET'])
def perfil_alumno (dni):
    return cargar_perfil_alumno (dni)

@profesor_bp.route('/perfil_alumno/<dni>', methods=['POST'])
def subir_comentario (dni):
    return subir_comentario_alumnoXclase (dni)