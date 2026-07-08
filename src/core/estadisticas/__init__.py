from sqlalchemy import func
from src.core.database import db
from src.core.usuarios.usuarios import Usuario, RolUsuario
from datetime import datetime,timedelta
from src.core.pagos.pagos import Pago
from collections import defaultdict

import enum

class Mes(enum.Enum):
        ENERO = 1
        FEBRERO = 2
        MARZO = 3
        ABRIL = 4
        MAYO = 5
        JUNIO = 6
        JULIO = 7
        AGOSTO = 8
        SEPTIEMBRE = 9
        OCTUBRE = 10
        NOVIEMBRE = 11
        DICIEMBRE = 12
        
        @property
        def nombre(self):
            return self.name.capitalize()

def obtener_registros_mensuales(año):
    return (
        db.session.query(
            func.extract("month", Usuario.fecha_creacion).label("mes"),
            func.count(Usuario.id).label("cantidad")
        )
        .filter(
            Usuario.rol == RolUsuario.CLIENTE,
            Usuario.eliminado == False,
            func.extract("year", Usuario.fecha_creacion) == año
        )
        .group_by("mes")
        .order_by("mes")
        .all()
    )


def preparar_registros_para_grafico(registros_db, anio):
    datos = {
        int(r.mes): r.cantidad
        for r in registros_db
    }

    hoy = datetime.now()
    ultimo_mes = hoy.month if anio == hoy.year else 12

    registros = []

    for mes in range(1, ultimo_mes + 1):
        registros.append({
            "mes": Mes(mes).nombre,
            "cantidad": datos.get(mes, 0)
        })

    total = sum(registro["cantidad"] for registro in registros)

    return registros, total


def obtener_anios_disponibles():
    return [
        int(año)
        for (año,) in db.session.query(
            func.extract("year", Usuario.fecha_creacion)
        )
        .filter(
            Usuario.rol == RolUsuario.CLIENTE,
            Usuario.eliminado == False
        )
        .distinct()
        .order_by(func.extract("year", Usuario.fecha_creacion))
        .all()
    ]

def obtener_ganancias_mensuales(anio):
    return (
        db.session.query(
            func.extract("month", Pago.fecha_creacion).label("mes"),
            func.sum(Pago.monto_total).label("total")
        )
        .filter(
            func.extract("year", Pago.fecha_creacion) == anio
        )
        .group_by("mes")
        .order_by("mes")
        .all()
    )

def obtener_ganancias_periodo(desde: str, hasta: str):
    fecha_desde = datetime.strptime(desde, "%Y-%m-%d")

    # Incluye todo el día seleccionado
    fecha_hasta = datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=1)

    return (
        db.session.query(Pago)
        .filter(
            Pago.fecha_creacion >= fecha_desde,
            Pago.fecha_creacion < fecha_hasta
        )
        .order_by(Pago.fecha_creacion)
        .all()
    )


def preparar_ganancias_para_grafico(ganancias_db, fecha_desde, fecha_hasta):

    datos = {}

    for pago in ganancias_db:
        clave = (
            pago.fecha_creacion.year,
            pago.fecha_creacion.month
        )
        datos[clave] = datos.get(clave, 0) + pago.monto_total

    desde = datetime.strptime(fecha_desde, "%Y-%m-%d")
    hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d")

    actual = datetime(desde.year, desde.month, 1)

    ganancias = []

    while actual <= hasta:

        ganancias.append({
            "mes": f"{Mes(actual.month).nombre} {actual.year}",
            "total": datos.get(
                (actual.year, actual.month),
                0
            )
        })

        if actual.month == 12:
            actual = datetime(actual.year + 1, 1, 1)
        else:
            actual = datetime(actual.year, actual.month + 1, 1)

    return ganancias