import random
from src.core.usuarios.usuarios import Usuario
from src.core.usuarios.usuarios import RolUsuario
from src.core.usuarios.usuarios import EstadoUsuario as Estado
from src.core.usuarios.usuarios import EstadoAptoFisico as EstadoApto

class UsuarioSeeder:
    def __init__(self, db):
        self.db = db
    
    def run(self):
        print("Insertando 20 usuarios de prueba...")

        roles = [RolUsuario.CLIENTE, RolUsuario.RECEPCIONISTA, RolUsuario.PROFESOR, RolUsuario.ADMINISTRADOR]
        for i in range(20):
            nombre = f"Usuario {i}"
            apellido = f"Apellido {i}"
            dni = f"{random.randint(10000000, 99999999)}"
            email = f"user{i}@gmail.com"
            password = f"password{i}"
            rol = random.choice(roles)
            estado = Estado.PENDIENTE
            direccion = f"Direccion {i}"
            telefono = f"123456789{i}"
            fecha_nacimiento = f"1990-01-{i:02d}"
            estado_apto_fisico = EstadoApto.SIN_CARGAR

            usuario = Usuario(
                nombre=nombre,
                apellido=apellido,
                dni=dni, 
                email=email, 
                password=password, 
                rol=rol, 
                estado=estado, 
                direccion=direccion, 
                telefono=telefono, 
                fecha_nacimiento=fecha_nacimiento,
                estado_apto_fisico=estado_apto_fisico
            )
            
            print(f"Usuario creado: {usuario.nombre} con rol {usuario.rol}")
            self.db.session.add(usuario)

        self.db.session.commit()
        print("¡Se han guardado los 10 usuarios con éxito!")