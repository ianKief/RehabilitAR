import random, datetime
from src.core.usuarios.usuarios import Usuario, Cliente, Profesor, Administrador, Recepcionista
from src.core.usuarios.usuarios import RolUsuario
from src.core.usuarios.usuarios import EstadoUsuario as Estado
from src.core.usuarios.usuarios import EstadoAptoFisico as EstadoApto

class UsuarioSeeder:
    def __init__(self, db):
        self.db = db
    
    def run(self):
        print("Insertando 20 usuarios de prueba...")

        clases_por_rol = {
            RolUsuario.CLIENTE: Cliente,
            RolUsuario.PROFESOR: Profesor,
            RolUsuario.ADMINISTRADOR: Administrador,
            RolUsuario.RECEPCIONISTA: Recepcionista
    }
        for i in range(20):
            nombre = f"Usuario {i}"
            apellido = f"Apellido {i}"
            dni = f"{random.randint(10000000, 99999999)}"
            email = f"user{i}@gmail.com"
            password = f"password{i}"
            estado = Estado.PENDIENTE
            direccion = f"Direccion {i}"
            telefono = f"123456789{i}"
            fecha_nacimiento = datetime.datetime(1990, 1, (i % 28) + 1)

            rol = random.choice(list(RolUsuario))
            clase = clases_por_rol[rol]

            usuario = clase(
                nombre=nombre,
                apellido=apellido,
                dni=dni, 
                email=email, 
                password=password, 
                estado=estado, 
                direccion=direccion, 
                telefono=telefono, 
                fecha_nacimiento=fecha_nacimiento,
            )
            
            print(f"Usuario creado: {usuario.nombre} con rol {usuario.rol}")
            self.db.session.add(usuario)

        self.db.session.commit()
        print("¡Se han guardado los 20 usuarios con éxito!")