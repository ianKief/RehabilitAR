import random, datetime
from src.core.usuarios.usuarios import Usuario, Administrador, Cliente, Profesor, Recepcionista, AptoFisico, EstadoAptoFisico
from src.core.usuarios.usuarios import RolUsuario
from src.core.usuarios.usuarios import EstadoUsuario as Estado

class UsuarioSeeder:
    def __init__(self, db):
        self.db = db
    
    def run(self):
        print("🌱 Poblando usuarios...")
        try:
            # 1. Creación del Administrador por defecto
            admin_existente = self.db.session.query(Usuario).filter_by(email='pruebasrehabilitar@gmail.com').first()
            if not admin_existente:
                admin = Administrador(
                    nombre = "Admin",
                    apellido = "Admin",
                    dni = "12345678",
                    email = "pruebasrehabilitar@gmail.com",
                    password = "123456",
                    estado = Estado.ACTIVO
                )
                self.db.session.add(admin)

            # 2. Creación del Cliente de prueba con Apto Físico Aceptado
            cliente_existente = self.db.session.query(Usuario).filter_by(email='clienteprueba@gmail.com').first()
            if not cliente_existente:
                cliente = Cliente(
                    nombre="Cliente",
                    apellido="Prueba",
                    dni="87654321",
                    email="clienteprueba@gmail.com",
                    password="123456",
                    estado=Estado.ACTIVO,
                )
                self.db.session.add(cliente)
                self.db.session.flush() # Flush para obtener el ID sin cerrar la transacción
                
                apto = AptoFisico(
                    id_cliente=cliente.id,
                    estado=EstadoAptoFisico.ACEPTADO,
                )
                self.db.session.add(apto)

            # 3. Creación del Profesor de prueba
            profesor_existente = self.db.session.query(Usuario).filter_by(email='profesorprueba@gmail.com').first()
            if not profesor_existente:
                profesor = Profesor(
                    nombre="Profesor",
                    apellido="Prueba",
                    dni="33333333",
                    email="profesorprueba@gmail.com",
                    password="123456",
                    estado=Estado.ACTIVO,
                    id_especialidad=1
                )
                self.db.session.add(profesor)

            # Si ya existen los 3 usuarios base, no creamos los de prueba
            if admin_existente and cliente_existente and profesor_existente:
                print("💡 Usuarios base ya existentes, no se realizaron cambios.")
                return

            usuarios_a_crear = []
            roles = [RolUsuario.CLIENTE, RolUsuario.RECEPCIONISTA, RolUsuario.PROFESOR]
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
                fecha_nacimiento = datetime.datetime(1990, 1, (i % 28) + 1)

                datos_usuario = dict(
                    nombre=nombre,
                    apellido=apellido,
                    dni=dni, 
                    email=email, 
                    password=password, 
                    estado=estado, 
                    direccion=direccion, 
                    telefono=telefono,
                    fecha_nacimiento= fecha_nacimiento
                )

                if rol == RolUsuario.CLIENTE:
                    usuario = Cliente(**datos_usuario)
                elif rol == RolUsuario.PROFESOR:
                    usuario = Profesor(**datos_usuario)
                else:
                    usuario = Recepcionista(**datos_usuario)
                
                usuarios_a_crear.append(usuario)

            self.db.session.add_all(usuarios_a_crear)
            self.db.session.commit()
            print(f"✅ Usuarios poblados con éxito (3 base + {len(usuarios_a_crear)} de prueba).")
        except Exception as e:
            self.db.session.rollback()
            print(f"❌ Error al poblar usuarios: {e}")


class AdminSeeder:
    def __init__(self, db):
        self.db = db

    def run(self):
        # 1. Creación del Administrador por defecto
        admin_existente = self.db.session.query(Usuario).filter_by(email='pruebasrehabilitar@gmail.com').first()
        if not admin_existente:
            admin = Administrador(
                nombre = "Admin",
                apellido = "Admin",
                dni = "12345678",
                email = "pruebasrehabilitar@gmail.com",
                password = "123456",
                estado = Estado.ACTIVO
            )
            self.db.session.add(admin)
            self.db.session.commit()
            print("Admin por defecto creado con éxito")