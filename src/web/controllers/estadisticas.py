from flask import Blueprint,render_template,request
from src.web.helpers.decorator import requiere_rol
from datetime import datetime
from src.core.estadisticas import (
    obtener_registros_mensuales,
    preparar_registros_para_grafico,
    obtener_ganancias_mensuales,
    preparar_ganancias_para_grafico,
    obtener_asistencias_mensuales,
    preparar_asistencias_para_grafico,
    obtener_suspendidos_mensuales,
    preparar_suspendidos_para_grafico,
    obtener_anios_disponibles
)

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
        fecha_desde_default=ganancias["fecha_desde_default"],
        fecha_hasta_default=ganancias["fecha_hasta_default"],

        current_path=request.path
    )


def obtener_datos_registros():

    anios = obtener_anios_disponibles()
    is_search = request.args.get('is_search')

    anio = request.args.get(
        "anio",
        default=datetime.now().year,
        type=int
    )

    # Nuevos registros
    registros_db = obtener_registros_mensuales(anio)
    registros, total_clientes = preparar_registros_para_grafico(registros_db, anio)
    
    # Ganancias
    ganancias_db = obtener_ganancias_mensuales(anio)
    ganancias, total_ganancias = preparar_ganancias_para_grafico(ganancias_db, anio)

    # Asistencias
    asistencias_db = obtener_asistencias_mensuales(anio)
    asistencias, total_presentes, total_ausentes = preparar_asistencias_para_grafico(asistencias_db, anio)

    # Suspendidos
    suspendidos_db = obtener_suspendidos_mensuales(anio)
    suspendidos, total_suspendidos = preparar_suspendidos_para_grafico(suspendidos_db, anio)

    return render_template(
        "estadisticas/listar.html",
        registros=registros,
        total_clientes=total_clientes,
        ganancias=ganancias,
        total_ganancias=total_ganancias,
        asistencias=asistencias,
        total_presentes=total_presentes,
        total_ausentes=total_ausentes,
        suspendidos=suspendidos,
        total_suspendidos=total_suspendidos,
        anios=anios,
        anio_seleccionado=anio,
        is_search=is_search
    )

    total_ganancias = sum(
        pago.monto_total
        for pago in ganancias_db
    )

    return {
        "ganancias": ganancias,
        "total_ganancias": total_ganancias,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "fecha_desde_default": fecha_desde_default,
        "fecha_hasta_default": fecha_hasta_default
    }