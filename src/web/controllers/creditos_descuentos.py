from flask import Blueprint, render_template,request
from src.web.helpers.decorator import requiere_rol
from src.core.creditos_descuentos import obtener_creditos_descuentos


bp = Blueprint(
    "creditos_descuentos",
    __name__,
    url_prefix="/creditos_descuentos"
)

@bp.route("/", methods=["GET"])
@requiere_rol(["ADMINISTRADOR"])
def listar_creditos_descuentos():

    dni = request.args.get("dni")

    beneficios = obtener_creditos_descuentos(dni)

    return render_template(
        "creditos_descuentos/listar_creditos_descuentos.html",
        beneficios=beneficios
    )