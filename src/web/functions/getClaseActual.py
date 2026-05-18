from src.web.objects.Clase import Clase
from datetime import datetime

def getClaseActual (dni_profesor):
    return Clase ("Espalda", "2026-03-01", datetime.now().replace(hour=8, minute=0, second=0), datetime.now().replace(hour=10, minute=0, second=0))
