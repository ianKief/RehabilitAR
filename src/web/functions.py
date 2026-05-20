def es_dni (dni):
    return dni.isnumeric() and (len(dni) > 6) and (len(dni) < 9)

