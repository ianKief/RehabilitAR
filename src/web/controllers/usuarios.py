import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, request
from src.core.usuarios import crear_usuario as crear, listar_usuarios as listar, obtener_usuario_por_id_core, actualizar_rol_usuario
from src.core.usuarios.usuarios import EstadoAptoFisico
from src.web.helpers.decorator import requiere_rol
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from src.core.database import db

users_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@users_bp.route('/crear', methods=['GET', 'POST'])
@requiere_rol(['ADMINISTRADOR'])
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
    
    return render_template('usuarios/crear.html')

@users_bp.route('/lista', methods=['GET'])
@requiere_rol(['ADMINISTRADOR'])
def listar_usuarios():
    nombre_search = request.args.get('nombre', '').strip()
    apellido_search = request.args.get('apellido', '').strip()
    dni_search = request.args.get('dni', '').strip()
    email_search = request.args.get('email', '').strip()
    rol_search = request.args.get('rol', '').strip()
    estado_search = request.args.get('estado', '').strip()

    is_search = request.args.get('is_search')

    if is_search:
        if not any([nombre_search, apellido_search, dni_search, email_search, rol_search, estado_search]):
            flash("Debe ingresar al menos un filtro", "warning")
            return redirect(url_for('usuarios.listar_usuarios'))
        
        usuarios = listar(nombre=nombre_search, apellido=apellido_search, dni=dni_search, email=email_search, rol=rol_search, estado=estado_search)
    else:
        usuarios = listar()
    
    return render_template(
        'usuarios/lista_usuarios.html', 
        usuarios=usuarios,
        nombre_search=nombre_search,
        apellido_search=apellido_search,
        dni_search=dni_search,
        email_search=email_search,
        rol_search=rol_search,
        estado_search=estado_search
    )

@users_bp.route('/detalle/<int:id>', methods=['GET'])
@requiere_rol(['ADMINISTRADOR'])
def detalle_usuario(id):
    usuario = obtener_usuario_por_id_core(id)
    
    if not usuario:
        flash("El usuario solicitado no existe o fue eliminado.", "danger")
        return redirect(url_for('usuarios.listar_usuarios'))
    
    return render_template('usuarios/detalle_usuario.html', usuario=usuario)

@users_bp.route('/<int:id>/cambiar_rol', methods=['POST'])
@requiere_rol(['ADMINISTRADOR'])
def cambiar_rol(id):
    nuevo_rol = request.form.get('rol')
    
    try:
        actualizar_rol_usuario(id, nuevo_rol)
        flash("El rol del usuario fue actualizado con éxito.", "success")
        
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        db.session.rollback() 
        flash("Ocurrió un error inesperado al actualizar el rol.", "danger")
        
    return redirect(url_for('usuarios.detalle_usuario', id=id))
@users_bp.route('/perfil')
def perfil():
    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesion para ver tu perfil.", "warning")
        return redirect(url_for('auth.login'))
    
    usuario = obtener_usuario_por_id_core(user_id)

    if not usuario:
        session.clear()
        return redirect(url_for('auth.login'))
    
    dias_restantes = 0
    if usuario.estado_apto_fisico and usuario.estado_apto_fisico.name == 'ACEPTADO' and usuario.fecha_apto_fisico:
        fecha_vencimiento = usuario.fecha_apto_fisico + timedelta(days=365)
        dias_restantes = (fecha_vencimiento - datetime.now()).days
    
    return render_template('usuarios/perfil.html', usuario=usuario, dias_restantes=dias_restantes)

allowed_extensions = ('pdf', 'jpeg', 'jpg', 'png')
@users_bp.route('/perfil/subir_apto', methods=['POST'])
def subir_apto():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return redirect(url_for('auth.login'))
    
    usuario = obtener_usuario_por_id_core(usuario_id)
    if not usuario:
        return redirect(url_for('auth.login'))
    
    if usuario.estado_apto_fisico and usuario.estado_apto_fisico.name == 'ACEPTADO' and usuario.fecha_apto_fisico:
        fecha_vencimiento = usuario.fecha_apto_fisico + timedelta(days=365)
        if fecha_vencimiento > datetime.today():
            flash("Ya posee un apto físico aprobado actualmente", "danger")
            return redirect(url_for('usuarios.perfil'))
        
    if 'apto_fisico' not in request.files:
        flash("No se encontro ningun archivo.", "danger")
        return redirect(url_for('usuarios.perfil'))

    archivo = request.files.get('apto_fisico')
    if archivo.filename == '':
        flash("No seleccionaste ningún archivo", "warning")
        return redirect(url_for('usuarios.perfil'))
    
    if not archivo.filename.lower().endswith(allowed_extensions):
        flash("El tipo de archivo ingresado no es compatible", "danger")
        return redirect(url_for('usuarios.perfil'))
    
    if archivo and archivo.filename != '':
        nombre_archivo_apto = secure_filename(archivo.filename)
        ruta_destino = os.path.join(os.getcwd(), 'src', 'web', 'static', 'uploads', 'aptos_fisicos')

        os.makedirs(ruta_destino, exist_ok=True)

        archivo.save(os.path.join(ruta_destino, nombre_archivo_apto))

        usuario.ruta_apto_fisico = f"uploads/aptos_fisicos/{nombre_archivo_apto}"
        usuario.estado_apto_fisico = EstadoAptoFisico.EN_REVISION
        usuario.fecha_apto_fisico = datetime.today()

        db.session.commit()

        flash("Tu apto fisico fue subido exitosamente y esta pendiente de aprobacion", "success")
        return redirect(url_for('usuarios.perfil'))

    return redirect(url_for('usuarios.perfil'))