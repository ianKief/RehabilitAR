from src.web.objects.Clase import Clase
from src.web.objects.AsistenciaAlumno import AsistenciaAlumno
from src.web.functions.conseguirListaAlumnos import conseguirListaAlumnos
from datetime import datetime

def  conseguirTodasLasAsistenciasAlumnos (dni_profesor):

    clase1 = Clase ("Espalda", "2026-03-01", datetime.now().replace(hour=8, minute=0, second=0), datetime.now().replace(hour=10, minute=0, second=0))
    clase2 = Clase ("Rodilla", "2026-04-02", datetime.now().replace(hour=14, minute=0, second=0), datetime.now().replace(hour=15, minute=0, second=0))
    clase3 = Clase ("Codo", "2025-07-22", datetime.now().replace(hour=16, minute=30, second=0), datetime.now().replace(hour=19, minute=0, second=0))

    lista_alumnos = conseguirListaAlumnos(dni_profesor)

    comentario_pedro = "Llegó tarde"
    comentario_julian1 = "Nada que comentar"
    comentario_julian2 = "Sigue sin haber nada que comentar"
    comentario_julian = [comentario_julian1, comentario_julian2]

    asistencia1 = AsistenciaAlumno(lista_alumnos[0], clase1, "presente", comentarios=[comentario_pedro])
    asistencia2 = AsistenciaAlumno(lista_alumnos[1], clase2, "ausente")
    asistencia3 = AsistenciaAlumno(lista_alumnos[2], clase3, "presente", comentarios=comentario_julian)
    
    return [asistencia1, asistencia2, asistencia3]

