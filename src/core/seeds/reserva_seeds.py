import random

from sqlalchemy import select

from src.core.database import db

from src.core.usuarios.usuarios import Usuario
from src.core.clases.clases import Clase
from src.core.reserva.reservas import Reserva, Comentario

from src.core.clases import clase_tiene_lugar
from src.core.usuarios import cliente_tiene_horario_disponible

class ReservaSeeder:
    """ Dependencias: ClaseSeeder, UsuarioSeeder.
    Recomendaciones adicionales: ClaseProfesorSeeder
    """
    def __init__(self, db):
        self.db = db

    def devolver_clientes():
        """Devuelve todos los clientes definidos en la anterior seed."""
        stmt = select(Usuario).filter(Usuario.rol == "cliente")
        return db.session.execute(stmt).scalars().all()

    def devolver_clases():
        """Devuelve todas las clases definidas en la anterior seed."""
        stmt = select(Clase)
        return db.session.execute(stmt).scalars().all()
    
    """Limitaciones a tener en cuenta:
    1. Una clase posee un límite de alumnos
    2. Un alumno solo puede estar anotado en una clase a la vez"""
    def run(self):
        print("Insertando una reserva a cada alumno...")
        clientes = self.devolver_clientes()
        clases = self.devolver_clases()

        for cliente in clientes:
            encontre = False
            while not encontre:
                clase = random.choice(clases)
                if (clase_tiene_lugar (clase) and (cliente_tiene_horario_disponible(clase))):
                    id_cliente = cliente.id
                    id_clase = clase.id
                    asiste = "ausente"

                    encontre = True

                    reserva = Reserva (
                        id_cliente=id_cliente,
                        id_clase=id_clase,
                        asiste=asiste
                    )

                    self.db.session.add(Reserva)
        self.db.session.commit()

class ComentarioSeeder:
    """Dependencias: ReservaSeeder"""
    def __init__(self, db):
        self.db = db
    
    def devolver_reservas ():
        stmt = select(Reserva)
        return db.session.execute(stmt).scalars().all()
    
    def run (self):
        print ("Insertando de 0 a dos comentarios por Reserva...")
        reservas = self.devolver_reservas()
        contador = 1
        for reserva in reservas:
            contenido = "Comentario", contador
            id_reserva = reserva.id
            comentario = Comentario(
               comentario=contenido,
               id_reserva=id_reserva
           )
            self.db.session.add(Comentario)
        self.db.session.commit()
