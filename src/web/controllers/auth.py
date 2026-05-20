from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime

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
        apto_fisico = request.form.get('apto_fisico') # Opcional
        password = request.form.get('password')
        
        # Validaciones
        # 1. Validar que no falte ningún campo obligatorio
        if not all([nombre, apellido, dni, telefono, fecha_nacimiento, direccion, email, password]):
            # Si falta algún campo obligatorio, podríamos mostrar un mensaje de error
            return render_template('auth/registro.html', error="Por favor, complete todos los campos obligatorios.")
        
        # 2. Validar mayoría de edad
        today = datetime.now()
        birthdate = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
        age = (today - birthdate).days // 365
        if age < 18:
            return render_template('auth/registro.html', error="Debes ser mayor de edad para registrarte.")

        # 3. Validar que el DNI/Email no existan en la Base de Datos
        # ...

        # 4. Validar formato de la contraseña
        if len(password) < 6:
            return render_template('auth/registro.html', error="La contraseña debe tener al menos 6 caracteres.")
        
        # 5. Validar formato del email
        allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com']
        if not email.endswith(tuple(allowed_domains)):
            return render_template('auth/registro.html', error="El correo electrónico debe ser del dominio @gmail.com, @hotmail.com o @outlook.com.")

        # 6. Validar que el archivo de apto físico sea del tipo permitido
        if apto_fisico:
            allowed_extensions = ['pdf', 'jpeg', 'png']
            if not apto_fisico.endswith(tuple(allowed_extensions)):
                return render_template('auth/registro.html', error="El archivo de apto físico debe ser PDF, JPEG o PNG.")
        
        # 7. Guardar el usuario con rol 'CLIENTE' y estado 'Pendiente'
        
        # Si todo sale bien, lo dejamos pendiente de verificación y enviamos al email un código de verificación. 
        # Se abre una nueva página para que el usuario ingrese el código de verificación. Si el código es correcto, se activa la cuenta y se redirige al home.
        return render_template('auth/verificacion.html')
    
    # Si es un GET (el usuario recién entra a la página), mostramos el formulario
    return render_template('auth/registro.html')