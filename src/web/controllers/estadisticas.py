from flask import Blueprint, current_app, flash,redirect,render_template,request,session,url_for
from src.web.helpers.decorator import requiere_rol
from datetime import datetime
from src.core.estadisticas import obtener_registros_mensuales,Mes,preparar_registros_para_grafico,obtener_anios_disponibles,obtener_ganancias_periodo,preparar_ganancias_para_grafico

bp = Blueprint ("estadisticas",__name__, url_prefix="/estadisticas")
@bp.route("/",methods=["GET"])
@requiere_rol(["ADMINISTRADOR"])

def listar_estadisticas():

    registros = obtener_datos_registros()
    ganancias = obtener_datos_ganancias()

    # suspendidos = obtener_datos_suspendidos()
    # asistencias = obtener_datos_asistencias()

    return render_template(
        "estadisticas/listar.html",

        # Registros
        registros=registros["registros"],
        total_clientes=registros["total_clientes"],
        anios=registros["anios"],
        anio_seleccionado=registros["anio_seleccionado"],

        # Ganancias
        ganancias=ganancias["ganancias"],
        total_ganancias=ganancias["total_ganancias"],
        fecha_desde=ganancias["fecha_desde"],
        fecha_hasta=ganancias["fecha_hasta"],

        current_path=request.path
    )


def obtener_datos_registros():

    anios = obtener_anios_disponibles()

    anio = request.args.get(
        "anio",
        default=datetime.now().year,
        type=int
    )

    registros_db = obtener_registros_mensuales(anio)

    registros, total_clientes = preparar_registros_para_grafico(
        registros_db,
        anio
    )

    return {
        "registros": registros,
        "total_clientes": total_clientes,
        "anios": anios,
        "anio_seleccionado": anio
    }


def obtener_datos_ganancias():

    fecha_desde = request.args.get(
        "desde",
        default=f"{datetime.now().year}-01-01"
    )

    fecha_hasta = request.args.get(
        "hasta",
        default=datetime.now().strftime("%Y-%m-%d")
    )

    ganancias_db = obtener_ganancias_periodo(
        fecha_desde,
        fecha_hasta
    )

    ganancias = preparar_ganancias_para_grafico(
        ganancias_db,
        fecha_desde,
        fecha_hasta
    )

    total_ganancias = sum(
        pago.monto_total
        for pago in ganancias_db
    )

    return {
        "ganancias": ganancias,
        "total_ganancias": total_ganancias,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta
    }