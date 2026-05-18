class Clase ():
    def __init__(self, nombre, fecha, hora_inicio, hora_fin):
        self.nombre = nombre
        self.fecha = fecha
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
    
    def nombreTieneTexto(self, texto):
        return texto in self.nombre
    
    def esDeFecha (self, fecha):
        return self.fecha == fecha

    def getHoraFin (self):
        return self.hora_fin.strftime("%H:%Mhs")
    
    def getHoraInicio (self):
        return self.hora_inicio.strftime("%H:%Mhs")