from src.web.objects.Alumno import Alumno

class AlumnoDetallado (Alumno):
    def __init__(self, nombre, apellido, dni, porcentaje_asistencias):
        super().__init__(nombre, apellido, dni)
        self.porcentaje_asistencias = porcentaje_asistencias