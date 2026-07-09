from sqlalchemy import func, case
from src.core.database import db
from src.core.usuarios.usuarios import Usuario, RolUsuario, EstadoUsuario
from src.core.pagos.pagos import Pago, EstadoPago
from src.core.reservas.reservas import Reserva, AsistenciaReserva
from src.core.clases.clases import Clase
from datetime import datetime
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


def obtener_ganancias_mensuales(anio):
    return (
        db.session.query(
            func.extract("month", Pago.fecha_creacion).label("mes"),
            func.sum(Pago.monto_total).label("total")
        )
        .filter(
            Pago.estado_pago == EstadoPago.COMPLETADO,
            func.extract("year", Pago.fecha_creacion) == anio
        )
        .group_by("mes")
        .order_by("mes")
        .all()
    )

def preparar_ganancias_para_grafico(ganancias_db, anio):
    datos = {
        int(r.mes): r.total
        for r in ganancias_db
    }

    hoy = datetime.now()
    ultimo_mes = hoy.month if anio == hoy.year else 12

    ganancias = []

    for mes in range(1, ultimo_mes + 1):
        ganancias.append({
            "mes": Mes(mes).nombre,
            "total": datos.get(mes, 0)
        })

    total = sum(ganancia["total"] for ganancia in ganancias)

    return ganancias, total


def obtener_asistencias_mensuales(anio):
    return (
        db.session.query(
            func.extract("month", Clase.fecha_clase).label("mes"),
            func.count(case((Reserva.asiste == AsistenciaReserva.PRESENTE, 1))).label("presentes"),
            func.count(case((Reserva.asiste == AsistenciaReserva.AUSENTE, 1))).label("ausentes")
        )
        .join(Clase, Reserva.id_clase == Clase.id)
        .filter(func.extract("year", Clase.fecha_clase) == anio)
        .group_by("mes")
        .order_by("mes")
        .all()
    )


def preparar_asistencias_para_grafico(asistencias_db, anio):
    datos_presentes = {int(r.mes): r.presentes for r in asistencias_db}
    datos_ausentes = {int(r.mes): r.ausentes for r in asistencias_db}

    hoy = datetime.now()
    ultimo_mes = hoy.month if anio == hoy.year else 12

    asistencias = []
    for mes in range(1, ultimo_mes + 1):
        asistencias.append({
            "mes": Mes(mes).nombre,
            "presentes": datos_presentes.get(mes, 0),
            "ausentes": datos_ausentes.get(mes, 0)
        })
    
    total_presentes = sum(item["presentes"] for item in asistencias)
    total_ausentes = sum(item["ausentes"] for item in asistencias)

    return asistencias, total_presentes, total_ausentes


def obtener_suspendidos_mensuales(anio):
    return (
        db.session.query(
            func.extract("month", Usuario.fecha_modificacion).label("mes"),
            func.count(Usuario.id).label("cantidad")
        )
        .filter(
            Usuario.rol == RolUsuario.CLIENTE,
            Usuario.estado == EstadoUsuario.BLOQUEADO,
            func.extract("year", Usuario.fecha_modificacion) == anio
        )
        .group_by("mes")
        .order_by("mes")
        .all()
    )


def preparar_suspendidos_para_grafico(suspendidos_db, anio):
    datos = {
        int(r.mes): r.cantidad
        for r in suspendidos_db
    }

    hoy = datetime.now()
    ultimo_mes = hoy.month if anio == hoy.year else 12

    suspendidos = []
    for mes in range(1, ultimo_mes + 1):
        suspendidos.append({
            "mes": Mes(mes).nombre,
            "cantidad": datos.get(mes, 0)
        })

    total = sum(item["cantidad"] for item in suspendidos)

    return suspendidos, total


def obtener_anios_disponibles():
    años_usuarios = [
        int(año)
        for (año,) in db.session.query(
            func.extract("year", Usuario.fecha_creacion)
        )
        .filter(
            Usuario.rol == RolUsuario.CLIENTE,
            Usuario.eliminado == False
        )
        .distinct()
        .all()
    ]
    años_pagos = [
        int(año)
        for (año,) in db.session.query(
            func.extract("year", Pago.fecha_creacion)
        )
        .filter(
            Pago.estado_pago == EstadoPago.COMPLETADO
        )
        .distinct()
        .all()
    ]
    años_clases = [
        int(año)
        for (año,) in db.session.query(
            func.extract("year", Clase.fecha_clase)
        )
        .distinct()
        .all()
    ]
    años_suspendidos = [
        int(año)
        for (año,) in db.session.query(
            func.extract("year", Usuario.fecha_modificacion)
        )
        .filter(
            Usuario.rol == RolUsuario.CLIENTE,
            Usuario.estado == EstadoUsuario.BLOQUEADO
        )
        .distinct()
        .all()
    ]
    
    años_totales = sorted(list(set(años_usuarios + años_pagos + años_clases + años_suspendidos)))
    return años_totales