from flask import Blueprint, render_template, request, redirect, url_for
from src.core.usuarios import crear_usuario, listar_usuarios

users_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@users_bp.route('/crear', methods=['GET', 'POST'])
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
            return render_template('usuarios/crear.html', error="Por favor, complete todos los campos obligatorios.")

        # 2. Validar que el password tenga al menos 6 caracteres
        if len(password) < 6:
            return render_template('usuarios/crear.html', error="La contraseña debe tener al menos 6 caracteres.")
        
        # 3. Validar formato del email
        allowed_domains = ['gmail.com', 'hotmail.com', 'outlook.com']
        if not email.endswith(tuple(allowed_domains)):
            return render_template('usuarios/crear.html', error="El correo electrónico debe ser del dominio @gmail.com, @hotmail.com o @outlook.com.")
        
        try:
            nuevo_usuario = crear_usuario(nombre=nombre, email=email, password=password, rol=rol)    
        except ValueError as e:
            return render_template('usuarios/crear.html', error=str(e))
        return render_template('usuarios/crear.html', success="Usuario creado correctamente.")
    
    return render_template('usuarios/crear.html')

@users_bp.route('/lista')
def listar_usuarios():
    usuarios = listar_usuarios()
    return render_template('usuarios/lista_usuarios.html', usuarios=usuarios)
        