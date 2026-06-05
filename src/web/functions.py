from datetime import datetime, timedelta

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