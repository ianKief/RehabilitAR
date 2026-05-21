from flask import Blueprint, render_template, request
from src.core.salas import listar_salas
 
bp = Blueprint("salas", __name__, url_prefix="/salas")

@bp.route("/")
def lista_salas():
    salas = listar_salas()
    return render_template("salas/listasalas.html", salas=salas,current_path=request.path)