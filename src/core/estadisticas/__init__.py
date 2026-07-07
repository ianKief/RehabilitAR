from sqlalchemy import func
from src.core.database import db
from src.core.usuarios.usuarios import Usuario, RolUsuario
from datetime import datetime
from dateutil.relativedelta import relativedelta
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