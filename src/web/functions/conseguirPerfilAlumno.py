# ESTA ES UNA FUNCIÓN TEMPORAL
from src.web.objects.AlumnoDetallado import AlumnoDetallado

def conseguirPerfilAlumno (dni_alumno):
    if (dni_alumno == "11111111"):
        return AlumnoDetallado("Pedro", "Perez", "11111111", 1/2)
    elif (dni_alumno == "22222222"):
        return AlumnoDetallado("Martin", "Maroni", "22222222", 1)
    elif (dni_alumno == "33333333"):
        AlumnoDetallado("Julian", "Serrano", "33333333", 2/3)
    
    return AlumnoDetallado("Momonto", "Magoya", "00000000", 3/4)