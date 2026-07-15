from sqlalchemy import select, desc

from src.core.database import db
from src.core.creditos_descuentos.creditos_descuentos import (
    CreditoDescuento,
    TipoBeneficio
)



def obtener_creditos_descuentos(dni=None):

    stmt = (
        select(CreditoDescuento)
        .order_by(desc(CreditoDescuento.fecha_creacion))
    )

    if dni:
        from src.core.usuarios.usuarios import Cliente

        stmt = (
            stmt
            .join(Cliente, Cliente.id == CreditoDescuento.id_cliente)
            .where(Cliente.dni == dni)
        )

    resultado = db.session.execute(stmt)

    return resultado.scalars().all()

def crear_credito_descuento(
    id_cliente,
    id_cancelacion,
    tipo,
    cantidad,
    motivo="Clase cancelada"
):

    beneficio_historial = CreditoDescuento(
        id_cliente=id_cliente,
        id_cancelacion=id_cancelacion,
        tipo=tipo,
        cantidad=cantidad,
        motivo=motivo
    )

    db.session.add(beneficio_historial)


    # Crear beneficio usable en pagos
    from src.core.pagos.pagos import Beneficio

    if tipo == TipoBeneficio.CREDITO:

        beneficio_pago = Beneficio(
            id_cliente=id_cliente,
            tipo=TipoBeneficio.CREDITO.name,
            descripcion=motivo
        )

    elif tipo == TipoBeneficio.DESCUENTO:

        beneficio_pago = Beneficio(
            id_cliente=id_cliente,
            tipo=TipoBeneficio.DESCUENTO.name,
            descripcion=motivo,
            porcentaje_descuento=0.20
        )

    else:
        raise ValueError(f"Tipo de beneficio inválido: {tipo}")


    db.session.add(beneficio_pago)

    return beneficio_historial


def generar_beneficio_por_cancelacion(cancelacion):

    reserva = cancelacion.reserva
    cliente = reserva.cliente
    clase = reserva.clase

    from datetime import datetime, timedelta
    from src.core.pagos import estado_abono_usuario

    estado_abono = estado_abono_usuario(cliente.id)

    if estado_abono != "activo":
        return None

    fecha_hora_clase = datetime.combine(
        clase.fecha_clase,
        clase.horario
    )

    tiempo_restante = fecha_hora_clase - datetime.now()

    if clase.tipo == "Fija":

        if tiempo_restante >= timedelta(hours=48):

            return crear_credito_descuento(
                id_cliente=cliente.id,
                id_cancelacion=cancelacion.id,
                tipo=TipoBeneficio.CREDITO,
                cantidad="1",
                motivo="Cancelación de clase fija"
            )

        elif tiempo_restante >= timedelta(hours=24):

            return crear_credito_descuento(
                id_cliente=cliente.id,
                id_cancelacion=cancelacion.id,
                tipo=TipoBeneficio.DESCUENTO,
                cantidad="20%",
                motivo="Cancelación de clase fija"
            )

    return None