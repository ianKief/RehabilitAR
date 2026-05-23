from datetime import datetime, timedelta

def es_dni (dni):
    return dni.isnumeric() and (len(dni) > 6) and (len(dni) < 9)

def devolver_hora_fin (horario, duracion):

    print ("Hora de la clase:", horario)
    print ("Duración de la clase:", duracion)
    finalizacion = (
        datetime.combine(
            datetime.today(),
            horario
        )
        + timedelta(minutes=duracion)
    ).time()

    print ("Finalización de la clase:", finalizacion)
    return finalizacion