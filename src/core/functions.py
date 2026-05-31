from sqlalchemy import func, literal_column, Time, Date, exists, and_, text
from src.core.clases.clases import Clase
from src.core.pagos import Pago, ConceptoPago

def filtro_clase_actual ():
    """Devuelve dos filtros para filtrar que actualmente está sucediendo una clase. Para usar, hacer .filter(*filtro_clase_actual())"""
    
    hora_actual = devolver_hora_actual()

    return [
        func.current_date() == Clase.fecha_clase,

        hora_actual > Clase.horario,

        hora_actual < (
            Clase.horario
            +
            (
                Clase.duracion
                * literal_column(
                    "INTERVAL '1 minute'"
                )
            )
        )
    ]

def filtro_cliente_abonado (id_cliente):
    """Use este filtro cuando quiera comprobar en una función de BD si el cliente es abonado. .filter(*filtro_cliente_abonado)
    En la expresión SQL, comprueba si existe pago del cliente tal que sea un abono y se haya creado hace menos de un mes.
    NOTA: Pago posee un atributo fecha_fin. Por ahora no vi casos, pero si se diese que se pueden pagar varios meses de un pago de abono o que se puede empezar el abono en un momento distinto al del pago, la función queda fuera de onda."""
    return exists().where(
        and_(
            Pago.id_cliente == id_cliente,
            Pago.concepto_pago == ConceptoPago.ABONO,
            Pago.fecha_creacion >= (
                func.now()
                - text("INTERVAL '1 month'")
            )
        )
    )

def devolver_hora_actual ():
    """Devuelve la hora actual como objeto sqlalchemy.Time.
    Recomendable usar en reemplazo de func.now() para evitar incongruencias horarias"""
    return devolver_fecha_hora_actual().cast(Time)

def devolver_fecha_actual ():
    return devolver_fecha_hora_actual().cast(Date)

def devolver_fecha_hora_actual ():
    return func.timezone(
        'America/Argentina/Buenos_Aires',
        func.now()
    )
