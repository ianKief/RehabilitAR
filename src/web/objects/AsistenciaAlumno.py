class AsistenciaAlumno ():
    def __init__(self, alumno, clase, presencia, comentarios=[]):
        self.alumno = alumno
        self.clase = clase
        self.presencia = presencia
        self.comentarios = comentarios
    
    def tieneTexto (self, texto):
        return (self.alumno.nombreTieneTexto(texto) or self.comentariosTienenTexto(texto))
    
    def comentariosTienenTexto (self, texto):
        if (self.comentarios == []):
            return False
        for comentario in self.comentarios:
            if texto in comentario.lower():
                return True
    
    def esDeFecha (self, fecha):
        return self.clase.esDeFecha(fecha)
    
    def tieneComentarios (self):
        return self.comentarios!=[]
    
    def devolverTrueSiPasaFiltroDeEstado (self, estado):
        if estado == "seleccionar_todos":
            return True
        print ("estado:", estado, "presencia:", self.presencia)
        return estado == self.presencia