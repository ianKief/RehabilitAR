from src.web.objects.Clase import Clase
from src.web.objects.AsistenciaAlumno import AsistenciaAlumno
from src.web.functions.conseguirListaAlumnos import conseguirListaAlumnos

def conseguirTodasLasAsistenciasAlumnos (dni_profesor):
    clase1 = Clase ("Espalda", "20260301")
    clase2 = Clase ("Rodilla", "20260402")
    clase3 = Clase ("Codo", "20250722")

    lista_alumnos = conseguirListaAlumnos

    comentario_pedro = "Llegó tarde"
    comentario_julian1 = "Nada que comentar"
    comentario_julian2 = "Sigue sin haber nada que comentar"
    comentario_julian = [comentario_julian1, comentario_julian2]

    asistencia1 = AsistenciaAlumno(lista_alumnos[0], clase1, "Presente", comentarios=[comentario_pedro])
    asistencia2 = AsistenciaAlumno(lista_alumnos[1], clase2, "Ausente")
    asistencia3 = AsistenciaAlumno(lista_alumnos[2], clase3, "Presente", comentarios=comentario_julian)
    
    return [asistencia1, asistencia2, asistencia3]

