import random
from datetime import datetime, timedelta
from sqlalchemy import select, or_
from src.core.database import db
from src.core.usuarios.usuarios import Usuario, RolUsuario, EstadoUsuario

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
    # Si todo está libre, creamos el usuario
    nuevo_cliente = Usuario(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        telefono=telefono,
        fecha_nacimiento=fecha_nacimiento,
        direccion=direccion,
        email=email,
        password=password, 
        rol=RolUsuario.CLIENTE,
        estado=EstadoUsuario.PENDIENTE,
        ruta_apto_fisico=nombre_archivo_apto,
        codigo_verificacion=codigo_verificacion,
        codigo_verificacion_expira=tiempo_expiracion
    )

    db.session.add(nuevo_cliente)
    db.session.commit()
    db.session.refresh(nuevo_cliente)

    # Aca se enviaría el email con el código de verificación
    print(f"--- EMAIL SIMULADO ---")
    print(f"Para: {email}")
    print(f"Tu código de verificación para RehabilitAR es: {codigo_verificacion}")
    print(f"Válido hasta: {tiempo_expiracion}")
    print(f"----------------------")
    
    return nuevo_cliente

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