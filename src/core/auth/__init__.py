import random
from datetime import datetime, timedelta
from sqlalchemy import select, or_
from src.core.database import db
from src.core.usuarios.usuarios import Usuario, RolUsuario, EstadoUsuario, Cliente, AptoFisico, EstadoAptoFisico

def registrar_cliente(nombre, apellido, dni, telefono, fecha_nacimiento, direccion, email, password, nombre_archivo_apto=None):
    
    # Buscamos si hay algún usuario que tenga ESE email O ESE dni
    stmt = select(Usuario).filter(or_(Usuario.email == email, Usuario.dni == dni))
    usuario_existente = db.session.execute(stmt).scalar()
    
    if usuario_existente:
        if usuario_existente.email == email:
            raise ValueError("El correo electrónico ya está registrado.")
        if usuario_existente.dni == dni:
            raise ValueError("El DNI ingresado ya se encuentra en el sistema.")

    codigo_verificacion = str(random.randint(100000, 999999))
    tiempo_expiracion = datetime.now() + timedelta(minutes=15)

    nuevo_apto = None
    if nombre_archivo_apto:
        nuevo_apto = AptoFisico(archivo_ruta=nombre_archivo_apto, fecha=datetime.now(), estado=EstadoAptoFisico.SIN_CARGAR)
        db.session.add(nuevo_apto)
        db.session.flush()
        db.session.refresh(nuevo_apto)
    # Si todo está libre, creamos el usuario
    nuevo_cliente = Cliente(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        telefono=telefono,
        fecha_nacimiento=fecha_nacimiento,
        direccion=direccion,
        email=email,
        password=password, 
        estado=EstadoUsuario.PENDIENTE,
        apto_fisico=nuevo_apto,
        codigo_verificacion=codigo_verificacion,
        codigo_verificacion_expira=tiempo_expiracion
    )

    db.session.add(nuevo_cliente)
    db.session.flush()
    db.session.refresh(nuevo_cliente)
    
    return nuevo_cliente

def login(email, password):
    stmt = select(Usuario).filter(Usuario.email == email)
    usuario = db.session.execute(stmt).scalar()

    # Validaciones
    # 1. Cuenta inexistente
    if not usuario:
        raise ValueError("Inicio de sesión fallido: El correo ingresado no corresponde a ninguna cuenta")
    
    # 2. Cuenta bloqueada se desbloquea si ya pasó el tiempo de bloqueo
    if usuario.estado == EstadoUsuario.BLOQUEADO and usuario.bloqueado_hasta and datetime.now() > usuario.bloqueado_hasta:
        usuario.estado = EstadoUsuario.ACTIVO
        usuario.intentos_login = 0
        usuario.bloqueado_hasta = None
        db.session.commit()

    # 3. Cuenta bloqueada y todavia no paso el tiempo de bloqueo
    if usuario.estado == EstadoUsuario.BLOQUEADO:
        raise ValueError("Inicio de sesión fallido: Cuenta bloqueada por motivos de seguridad. Vuelva a intentar en {} minutos."
                         .format(int((usuario.bloqueado_hasta - datetime.now()).total_seconds() // 60) + 1))

    # 4. Cuenta pendiente de verificación
    if usuario.estado == EstadoUsuario.PENDIENTE:
        raise ValueError("Inicio de sesión fallido: La cuenta aún no ha sido verificada. Por favor, revise su correo para obtener el código de verificación.")
    
    # 5. Contraseña incorrecta
    if usuario.password != password:
        usuario.intentos_login += 1

        # 5.1. Alcanzó los 5 intentos fallidos
        if usuario.intentos_login >= 5:
            usuario.estado = EstadoUsuario.BLOQUEADO
            usuario.bloqueado_hasta = datetime.now() + timedelta(hours=1)
            db.session.commit()
            raise ValueError("Inicio de sesión fallido: Contraseña incorrecta. Por motivos de seguridad se ha bloqueado su cuenta por una hora")
        
        # 5.2. Aún no alcanza los 5 intentos fallidos
        db.session.commit()
        raise ValueError("Inicio de sesión fallido: Contraseña incorrecta. Te quedan {} intentos antes de que la cuenta sea bloqueada."
        .format(5 - usuario.intentos_login))

    # Si pasó todas las validaciones, se loguea exitosamente y se resetean los intentos de login
    usuario.intentos_login = 0
    usuario.bloqueado_hasta = None
    db.session.commit()        

    codigo_verificacion = str(random.randint(100000, 999999))
    tiempo_expiracion = datetime.now() + timedelta(minutes=15)

    usuario.codigo_verificacion = codigo_verificacion
    usuario.codigo_verificacion_expira = tiempo_expiracion
    usuario.intentos_codigo = 0

    db.session.flush()

    return usuario


def confirmar_codigo(user_id, codigo_ingresado):
    usuario = db.session.get(Usuario, user_id)
    if not usuario:
        raise ValueError("Usuario no encontrado.")
    
    # Validación 1: Código inválido por intentos
    if usuario.intentos_codigo >= 3:
        raise ValueError("Este código ya no es válido por superar el número máximo de intentos. Por favor, solicita uno nuevo.")
    
    # Validación 2: Código incorrecto
    if usuario.codigo_verificacion != codigo_ingresado:
        usuario.intentos_codigo += 1
        db.session.commit()

        # Validación 2.1: Si el usuario supera los 3 intentos, se invalida el código
        if usuario.intentos_codigo >= 3:
            usuario.codigo_verificacion = None
            db.session.commit()
            raise ValueError("Código incorrecto. Has superado el número máximo de intentos. Por favor, solicita uno nuevo.")
        intentos_restantes = 3 - usuario.intentos_codigo
        raise ValueError(f"El codigo ingresado es incorrecto. Te quedan {intentos_restantes} intentos.")

    # Validación 3: Código expirado
    if datetime.now() > usuario.codigo_verificacion_expira:
        raise ValueError("El codigo ha expirado. Por favor, solicita uno nuevo.")
    
    
    usuario.codigo_verificacion = None
    usuario.codigo_verificacion_expira = None
    usuario.intentos_codigo = 0
    usuario.estado = EstadoUsuario.ACTIVO

    db.session.commit()

    return True