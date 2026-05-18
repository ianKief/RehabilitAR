from flask import Blueprint, render_template, request, redirect, url_for

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/create', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        # Aca podemos manejar la creación del usuario
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        rol = request.form.get('rol')
        
        # Validaciones
        # 1. Validar que no falte ningun campo obligatorio
        if not all([nombre, email, password, rol]):
            # Si falta algun campo obligatorio, podriamos mostrar un mensaje de error
            return render_template('users/create.html', error="Por favor, complete todos los campos obligatorios.")
        
        # 2. Validar que el email no exista en la base de datos
        # ...
        
        # 3. Validar que el password tenga al menos 6 caracteres
        if len(password) < 6:
            return render_template('users/create.html', error="La contraseña debe tener al menos 6 caracteres.")
        
        # 4. Validar formato del email
        allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com']
        if not email.endswith(tuple(allowed_domains)):
            return render_template('users/create.html', error="El correo electrónico debe ser del dominio @gmail.com, @hotmail.com o @outlook.com.")
        
        return render_template('users/create.html', success="Usuario creado correctamente.")
    
    return render_template('users/create.html')
        