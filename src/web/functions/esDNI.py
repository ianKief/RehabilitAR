def esDNI (dni):
    return dni.isnumeric() and (len(dni) > 6) and (len(dni) < 9)