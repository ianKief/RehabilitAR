from flask import Blueprint, current_app, flash,redirect,render_template,request,session,url_for
from src.web.helpers.decorator import requiere_rol
from datetime import datetime
from src.core.estadisticas import obtener_registros_mensuales,Mes,preparar_registros_para_grafico,obtener_anios_disponibles

bp = Blueprint ("estadisticas",__name__, url_prefix="/estadisticas")
@bp.route("/",methods=["GET"])
@requiere_rol(["ADMINISTRADOR"])

def listar_estadisticas():
    anios = obtener_anios_disponibles()

    anio = request.args.get(
        "anio",
        default=datetime.now().year,
        type=int
    )

    registros_db = obtener_registros_mensuales(anio)

    registros,total_clientes = preparar_registros_para_grafico(registros_db, anio)
    
    return render_template(
        "estadisticas/listar.html",
        registros=registros,
        anios=anios,
        total_clientes=total_clientes,
        anio_seleccionado=anio,
        current_path=request.path
    )
