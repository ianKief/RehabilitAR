from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.core.usuarios import crear_usuario as crear, listar_usuarios as listar
from src.web.helpers.decorator import requiere_rol

users_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@users_bp.route('/crear', methods=['GET', 'POST'])
@requiere_rol(['ADMIN'])
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
            nuevo_usuario = crear(nombre=nombre, email=email, password=password, rol=rol)    
        except ValueError as e:
            flash(str(e), 'error')
            return render_template('usuarios/crear.html')
        
        flash("Usuario creado con éxito.", "success")
        return render_template('usuarios/crear.html')

@users_bp.route('/lista')
@requiere_rol(['ADMIN'])
def listar_usuarios():
    usuarios = listar()
    return render_template('usuarios/lista_usuarios.html', usuarios=usuarios)
        