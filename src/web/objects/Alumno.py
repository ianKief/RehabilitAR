class Alumno ():
    def __init__(self, nombre, apellido, dni):
        self.nombre = nombre
        self.apellido = apellido
        self.dni = dni
    
    def nombreTieneTexto (self, texto):
        return texto in self.nombre.lower() or texto in self.apellido.lower() or texto in self.dni.lower()