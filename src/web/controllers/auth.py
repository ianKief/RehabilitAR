import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_mail import Message
from datetime import datetime
from werkzeug.utils import secure_filename
from src.core.auth import registrar_cliente as registrar_cliente_core, confirmar_codigo as confirmar_codigo_core, login as login_core
from src.core.usuarios import obtener_usuario_por_id_core
from src.core.database import db
from src.web import mail

# Creamos el Blueprint llamado 'auth'
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registrar_cliente():
    if session.get('usuario_id'):
        return redirect(url_for('home'))
    
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

            msg = Message(
                subject="RehabilitAR - Código de Verificación",
                recipients=[nuevo_cliente.email]
            )

            msg.body = f"""Hola {nuevo_cliente.nombre},
        
                    ¡Gracias por registrarte en RehabilitAR!

                    Tu código de verificación de 6 dígitos es: {nuevo_cliente.codigo_verificacion}

                    Por razones de seguridad, este código expirará en 15 minutos. 
                    Si no solicitaste este registro, por favor ignorá este correo.

                    Saludos,
                    El equipo de RehabilitAR."""

            mail.send(msg)

            db.session.commit()
            
            session['verificacion_user_id'] = nuevo_cliente.id
            session['verificacion_origen'] = 'registro'
            return redirect(url_for('auth.verificar'))
        except ValueError as e:
            db.session.rollback()
            return render_template('auth/registro.html', error=str(e))
        except Exception as e:
            db.session.rollback()
            return render_template('auth/registro.html', error="Ocurrió un error inesperado. Por favor, intente nuevamente.")

    # Si es un GET (el usuario recién entra a la página), mostramos el formulario
    return render_template('auth/registro.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('usuario_id'):
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validamos que el email y la contraseña no estén vacíos
        if not email or not password:
            return render_template('auth/login.html', error="Por favor, ingrese su correo electrónico y contraseña.")

        try:
            usuario = login_core(email, password)

            msg = Message(
                subject="RehabilitAR - Código de Verificación",
                recipients=[usuario.email]
            )
            msg.body = f"""Hola {usuario.nombre},

            Se ha solicitado iniciar sesión en tu cuenta. 
            Tu código de verificación de 6 dígitos es: {usuario.codigo_verificacion}

            Por razones de seguridad, este código expirará en 15 minutos.
            Si no solicitaste este inicio de sesión, por favor ignora este correo."""

            mail.send(msg)

            db.session.commit()

            session['verificacion_user_id'] = usuario.id
            session['verificacion_origen'] = 'login'
            return redirect(url_for('auth.verificar'))
        
        except ValueError as e:
            db.session.rollback()
            return render_template('auth/login.html', error=str(e))
        
        except Exception as e:
            db.session.rollback()
            return render_template('auth/login.html', error="Ocurrió un error inesperado. Por favor, intente nuevamente.")

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear() 
    
    flash("Has cerrado sesión de forma segura.", "success")
    return redirect(url_for('home'))

@auth_bp.route('/verificar', methods=['GET', 'POST'])
def verificar():
    # Sacamos el ID del usuario que se está registrando de la sesión
    user_id = session.get('verificacion_user_id')

    # Leemos de donde viene
    origen = session.get('verificacion_origen')
    
    if not user_id:
        return redirect(url_for('auth.registrar_cliente'))

    if request.method == 'POST':
        codigo = request.form.get('codigo_verificacion')
        
        try:
            confirmar_codigo_core(user_id, codigo)
            
            # Limpiamos la sesión del proceso de registro
            session.pop('verificacion_user_id', None)
            session.pop('verificacion_origen', None)

            if origen == 'registro':
                flash("Verificación exitosa. Ya podes iniciar sesión.", "success")
                return redirect(url_for('auth.login'))
            elif origen == 'login':
                usuario = obtener_usuario_por_id_core(user_id)
                session.permanent = True
                session['usuario_id'] = usuario.id
                session['rol'] = usuario.rol.name
                flash("Verificación exitosa. Bienvenido!", "success")
                return redirect(url_for('home'))
            
        except ValueError as e:
            return render_template('auth/verificacion.html', error=str(e))

    return render_template('auth/verificacion.html')