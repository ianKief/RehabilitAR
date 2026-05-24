from datetime import datetime, timedelta

from src.core.reserva import AsistenciaReserva

def es_dni (dni):
    return dni.isnumeric() and (len(dni) > 6) and (len(dni) < 9)

def devolver_hora_fin (horario, duracion):

    finalizacion = (
        datetime.combine(
            datetime.today(),
            horario
        )
        + timedelta(minutes=duracion)
    ).time()

    return finalizacion

def agrupacion_manual_de_datos_de_comentarios_por_asistencia_y_alumno (filas):
    """Para un resultado de una query con reservas, clientes y alumnos, hace una versión que agrupa los comentarios por reserva y les añade datos del cliente"""
    resultado = {}

    for reserva, cliente, comentario, clase in filas:
        if reserva.id not in resultado:
            resultado[reserva.id] = {
                "reserva": reserva,
                "cliente": cliente,
                "clase": clase,
                "comentarios": []
            }

        if comentario:
            resultado[
                reserva.id
            ]["comentarios"].append(comentario)

    return list(resultado.values())