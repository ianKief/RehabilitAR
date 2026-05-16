class Clase ():
    def __init__(self, nombre, fecha):
        self.nombre = nombre
        self.fecha = fecha
    
    def nombreTieneTexto(self, texto):
        return texto in self.nombre
    
    def esDeFecha (self, fecha):
        return self.fecha == fecha