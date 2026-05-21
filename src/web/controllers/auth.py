import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from werkzeug.utils import secure_filename
from src.core.auth import registrar_cliente as registrar_cliente_core
from src.core.auth import confirmar_codigo as confirmar_codigo_core

# Creamos el Blueprint llamado 'auth'
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registrar_cliente():
    if request.method == 'POST':
        # Acá capturamos los datos del formulario HTML
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        dni = request.form.get('dni')
        telefono = request.form.get('telefono')
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        direccion = request.form.get('direccion')
        email = request.form.get('email')
        apto_fisico = request.files.get('apto_fisico') # Opcional
        password = request.form.get('password')
        
        # Validaciones
        # 1. Validar que no falte ningún campo obligatorio
        if not all([nombre, apellido, dni, telefono, fecha_nacimiento, direccion, email, password]):
            return render_template('auth/registro.html', error="Por favor, complete todos los campos obligatorios.")
        
        # 2. Validar mayoría de edad
        today = datetime.now()
        birthdate = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        age = (today - birthdate).days // 365
        if age < 18:
            return render_template('auth/registro.html', error="Debes ser mayor de edad para registrarte.")

        # 3. Validar formato de la contraseña
        if len(password) < 6:
            return render_template('auth/registro.html', error="La contraseña debe tener al menos 6 caracteres.")
        
        # 4. Validar formato del email
        allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com']
        if not email.endswith(tuple(allowed_domains)):
            return render_template('auth/registro.html', error="El correo electrónico debe ser del dominio @gmail.com, @hotmail.com o @outlook.com.")

        # 5. Validar que el archivo de apto físico sea del tipo permitido
        nombre_archivo_apto = None
        if apto_fisico and apto_fisico.filename != '':
            allowed_extensions = ['pdf', 'jpeg', 'jpg', 'png']
            if not apto_fisico.filename.lower().endswith((allowed_extensions)):
                return render_template('auth/registro.html', error="El archivo de apto físico debe ser PDF, JPEG o PNG.")
            
            nombre_archivo_apto = secure_filename(apto_fisico.filename)
            ruta_destino = os.path.join(os.getcwd(), 'src', 'web', 'static', 'uploads', 'aptos_fisicos')

            os.makedirs(ruta_destino, exist_ok=True)

            apto_fisico.save(os.path.join(ruta_destino, nombre_archivo_apto))
        
        # Si todo está bien, se registra al cliente dejanlo pendiente de verificación
        try:
            nuevo_cliente = registrar_cliente_core(
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                telefono=telefono,
                fecha_nacimiento=birthdate,
                direccion=direccion,
                email=email,
                password=password,
                nombre_archivo_apto=nombre_archivo_apto
            )
            
            session['registro_user_id'] = nuevo_cliente.id
            return redirect(url_for('auth.verificar'))
        except ValueError as e:
            return render_template('auth/registro.html', error=str(e))

    # Si es un GET (el usuario recién entra a la página), mostramos el formulario
    return render_template('auth/registro.html')

@auth_bp.route('/verificar', methods=['GET', 'POST'])
def verificar():
    # Sacamos el ID del usuario que se está registrando de la sesión
    user_id = session.get('registro_user_id')
    
    if not user_id:
        return redirect(url_for('auth.registrar_cliente'))

    if request.method == 'POST':
        codigo = request.form.get('codigo_verificacion')
        
        try:
            confirmar_codigo_core(user_id, codigo)
            
            # Limpiamos la sesión del proceso de registro
            session.pop('registro_user_id', None)

            return redirect(url_for('home')) 
            
        except ValueError as e:
            return render_template('auth/verificacion.html', error=str(e))

    return render_template('auth/verificacion.html')