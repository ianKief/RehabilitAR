# ESTA ES UNA FUNCIÓN TEMPORAL
# Consigue alumnos que reservaron la clase
from src.web.objects.Alumno import Alumno

def conseguirListaAlumnos (dni_profesor):
    Pepe = Alumno("Pedro", "Perez", "11111111")
    Martin = Alumno("Martin", "Maroni", "22222222")
    Julian = Alumno("Julian", "Serrano", "33333333")
    return [Pepe, Martin, Julian]