class AsistenciaAlumno ():
    def __init__(self, alumno, clase, presencia, comentarios=[]):
        self.alumno = alumno
        self.clase = clase
        self.asistencia = presencia
        self.comentarios = comentarios