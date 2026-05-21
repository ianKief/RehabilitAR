from flask import Blueprint, request, jsonify
from datetime import datetime
from src.core.abonos.servicio import calcular_abono_mensual

bp = Blueprint("abonos", __name__, url_prefix="/abonos")

@bp.get("/calcular")
def calcular():
    data = request.get_json()
    anio = data["anio"]
    mes = data["mes"]
    dia_semana = data["dia_semana"]
    valor_abono = data["valor_abono"]

    fecha_contratacion = datetime.strptime(data["fecha_contratacion"], "%Y-%m-%d").date()

    resultado = calcular_abono_mensual(anio,mes,dia_semana,fecha_contratacion,valor_abono)

    return jsonify(resultado)