from flask import Blueprint
from src.web.helpers.decorator import requiere_rol

from src.web.controllers.profesor.presente_manual import registrar_asistencia_manual
from src.web.controllers.profesor.index_profesor import renderizar_index_profesor
from src.web.controllers.profesor.listado_alumnos import consultar_listado_alumnos
from src.web.controllers.profesor.perfil_alumno import cargar_perfil_alumno
from src.web.controllers.profesor.subir_comentario import subir_comentario_a_alumnoXclase
from src.web.controllers.profesor.ver_asistencias import ver_comentarios_y_asistencias
from src.web.controllers.profesor.mostrar_qr import mostrar_qr_en_pantalla

profesor_bp = Blueprint('profesor', __name__, url_prefix="/profesor")

@profesor_bp.route('/', methods=['GET'])
@requiere_rol(["PROFESOR"])
def index_profesor ():
    return renderizar_index_profesor()

@profesor_bp.route('/presente_manual', methods=['GET', 'POST'])
@requiere_rol(["PROFESOR"])
def presente_manual ():
    return registrar_asistencia_manual()

@profesor_bp.route('/listado_alumnos', methods=['GET'])
@requiere_rol(["PROFESOR"])
def listado_alumnos ():
    return consultar_listado_alumnos()

@profesor_bp.route('/perfil_alumno/<dni>', methods=['GET'])
@requiere_rol(["PROFESOR"])
def perfil_alumno (dni):
    return cargar_perfil_alumno (dni)

@profesor_bp.route('/perfil_alumno/<dni>', methods=['POST'])
@requiere_rol(["PROFESOR"])
def subir_comentario (dni):
    return subir_comentario_a_alumnoXclase (dni)

@profesor_bp.route('/ver_asistencias', methods=['GET'])
@requiere_rol(["PROFESOR"])
def ver_asistencias ():
    return ver_comentarios_y_asistencias ()

@profesor_bp.route("/clase/<int:id>/qr")
@requiere_rol(["PROFESOR"])
def mostrar_qr (id):
    return mostrar_qr_en_pantalla (id)