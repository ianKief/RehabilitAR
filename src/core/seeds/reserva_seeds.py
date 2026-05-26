import random

from sqlalchemy import select

from src.core.database import db

from src.core.usuarios.usuarios import Cliente
from src.core.clases.clases import Clase
from src.core.reservas.reservas import Reserva, Comentario, AsistenciaReserva

from src.core.clases import clase_tiene_lugar

class ReservaSeeder:
    """ Dependencias: ClaseSeeder, UsuarioSeeder.
    Recomendaciones adicionales: ClaseProfesorSeeder
    """
    def __init__(self, db):
        self.db = db

    def devolver_clientes(self):
        """Devuelve todos los clientes definidos en la anterior seed."""
        stmt = select(Cliente)
        return self.db.session.execute(stmt).scalars().all()

    def devolver_clases(self):
        """Devuelve todas las clases definidas en la anterior seed."""
        stmt = select(Clase)
        return self.db.session.execute(stmt).scalars().all()
    
    """Limitaciones a tener en cuenta:
    1. Una clase posee un límite de alumnos
    2. Un alumno solo puede estar anotado en una clase a la vez"""
    def run(self):
        print("Insertando una reserva a cada alumno...")
        clientes = self.devolver_clientes()
        clases = self.devolver_clases()
        i = 1

        for cliente in clientes:
            encontre = False
            while not encontre:
                clase = random.choice(clases)
                if clase_tiene_lugar (clase):
                    print ("Insertando reserva", i)
                    i+=1
                    encontre = True

                    id_cliente = cliente.id
                    id_clase = clase.id
                    asiste = AsistenciaReserva.AUSENTE

                    reserva = Reserva (
                        id_cliente=id_cliente,
                        id_clase=id_clase,
                        asiste=asiste
                    )

                    self.db.session.add(reserva)
        self.db.session.commit()

class ComentarioSeeder:
    """Dependencias: ReservaSeeder"""
    def __init__(self, db):
        self.db = db
    
    def devolver_reservas (self):
        stmt = select(Reserva)
        return db.session.execute(stmt).scalars().all()
    
    def run (self):
        print ("Insertando de 0 a dos comentarios por Reserva...")
        reservas = self.devolver_reservas()
        contador = 1
        for reserva in reservas:
            cantidad_comentarios = random.randint(0, 2)
            for _ in range(cantidad_comentarios):
                contenido = f"Comentario {contador}"
                comentario = Comentario(
                   comentario=contenido,
                   id_reserva=reserva.id
               )
                self.db.session.add(comentario)
                contador += 1
        self.db.session.commit()
