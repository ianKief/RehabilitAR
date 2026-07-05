import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, request
from src.core.usuarios import crear_usuario as crear, listar_usuarios as listar, obtener_aptos_en_revision, obtener_usuario_por_id_core, actualizar_rol_usuario, bloquear_usuario, habilitar_usuario, eliminar_usuario, revisar_y_aprobar_apto, revisar_y_rechazar_apto, modificar_usuario_core
from src.core.usuarios.usuarios import Usuario, EstadoAptoFisico, Cliente, AptoFisico
from src.web.helpers.decorator import requiere_rol
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from src.core.database import db
from flask_mail import Message
from src.web import mail

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
            # TODO enviar mail
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
    
    usuario = db.session.get(Usuario, user_id)

    if not usuario:
        session.clear()
        return redirect(url_for('auth.login'))
    
    dias_restantes = 0

    if isinstance(usuario, Cliente) and usuario.apto_fisico:
        apto = usuario.apto_fisico
        if apto.estado.name == 'ACEPTADO' and apto.fecha_carga:
            fecha_vencimiento = apto.fecha_carga + timedelta(days=365)
            dias_restantes = (fecha_vencimiento - datetime.now()).days

    print (usuario)
    
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
    
    if not isinstance(usuario, Cliente):
        flash("Solo los clientes pueden subir certificados médicos.", "danger")
        return redirect(url_for('usuarios.perfil'))
    
    apto = usuario.apto_fisico
    if apto and apto.estado.name == 'ACEPTADO' and apto.fecha_carga:
        fecha_vencimiento = apto.fecha_carga + timedelta(days=365)
        if fecha_vencimiento > datetime.now():
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
        nombre_archivo_apto = f"{usuario.dni}_{secure_filename(archivo.filename)}"
        ruta_destino = os.path.join(os.getcwd(), 'src', 'web', 'static', 'uploads', 'aptos_fisicos')

        os.makedirs(ruta_destino, exist_ok=True)

        archivo.save(os.path.join(ruta_destino, nombre_archivo_apto))

        if not usuario.apto_fisico:
            nuevo_apto = AptoFisico(
                ruta_archivo=nombre_archivo_apto,
                fecha_carga=datetime.now(),
                estado=EstadoAptoFisico.EN_REVISION
            )
            usuario.apto_fisico = nuevo_apto
        else:
            usuario.apto_fisico.ruta_archivo = nombre_archivo_apto
            usuario.apto_fisico.fecha_carga = datetime.now()
            usuario.apto_fisico.estado = EstadoAptoFisico.EN_REVISION

        db.session.commit()

        flash("Tu apto fisico fue subido exitosamente y esta pendiente de aprobacion", "success")
        return redirect(url_for('usuarios.perfil'))

    return redirect(url_for('usuarios.perfil'))

@users_bp.route('/<int:id>/bloquear', methods=['POST'])
@requiere_rol(['ADMINISTRADOR'])
def ruta_bloquear_usuario(id):
    try:
        bloquear_usuario(id, motivo="La administración ha bloqueado su usuario. Para más información acérquese a la administración.")
        flash("El usuario ha sido bloqueado y ya no tiene acceso al sistema.", "success")
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")
        
    return redirect(url_for('usuarios.detalle_usuario', id=id))

@users_bp.route('/<int:id>/habilitar', methods=['POST'])
@requiere_rol(['ADMINISTRADOR'])
def ruta_habilitar_usuario(id):
    try:
        habilitar_usuario(id)
        flash("El usuario ha sido habilitado exitosamente.", "success")
    except ValueError as e:
        # Acá atrapamos si tiene deudas y mostramos el mensaje de error
        flash(str(e), "warning") 
    except Exception as e:
        db.session.rollback()
        flash("Ocurrió un error inesperado.", "danger")
        print (str(e))
        
    return redirect(url_for('usuarios.detalle_usuario', id=id))

@users_bp.route('/<int:id>/eliminar', methods=['POST'])
@requiere_rol(['ADMINISTRADOR'])
def ruta_eliminar_usuario(id):
    # 1. Buscamos al usuario ANTES de borrarlo para rescatar su email
    usuario = obtener_usuario_por_id_core(id)
    
    if not usuario:
        flash("El usuario no existe o ya fue eliminado.", "danger")
        return redirect(url_for('usuarios.listar_usuarios'))
        
    email_destino = usuario.email
    nombre_usuario = usuario.nombre
    
    try:
        # 2. Lo eliminamos permanentemente
        eliminar_usuario(id)
        
        # 3. Armamos y enviamos el correo de notificación
        msg = Message(
            subject="RehabilitAR - Cuenta Eliminada",
            recipients=[email_destino]
        )
        msg.body = f"""Hola {nombre_usuario},

Te informamos que tu cuenta en el sistema RehabilitAR ha sido eliminada permanentemente por un Administrador.

Si crees que esto es un error o tenés alguna duda, por favor contactate con la administración.

Saludos,
El equipo de RehabilitAR."""

        mail.send(msg)
        
        # 4. Mostramos el mensaje exacto que pide tu HU
        flash("Cuenta eliminada con éxito.", "success")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar usuario o enviar correo: {e}")
        flash("Ocurrió un error inesperado al intentar eliminar la cuenta.", "danger")
        
    # 5. Redirigimos al listado porque el detalle del usuario ya no existe
    return redirect(url_for('usuarios.listar_usuarios'))

@users_bp.route("/aptos", methods=["GET"])
@requiere_rol(['ADMINISTRADOR'])
def listar_aptos_pendientes():
    """
    Renderiza el panel con la lista de aptos físicos que requieren revisión.
    """
    # Pasamos la sesión actual al core
    aptos_pendientes = obtener_aptos_en_revision(db.session)
    
    return render_template(
        "usuarios/aptos_pendientes.html", 
        aptos=aptos_pendientes
    )


@users_bp.route("/aptos/<int:id_apto>/aprobar", methods=["POST"])
@requiere_rol(['ADMINISTRADOR'])
def aprobar_apto(id_apto):
    """
    Ruta que se ejecuta al presionar 'Aceptar' en el panel del administrador.
    """
    try:
        revisar_y_aprobar_apto(db.session, id_apto)
        flash("El apto físico ha sido aprobado con éxito.", "success")
    except ValueError as e:
        # Capturamos las validaciones del Core (ej: si ya estaba procesado)
        flash(str(e), "danger")
    except Exception as e:
        # Fallos inesperados de base de datos
        flash("Ocurrió un error inesperado al procesar la aprobación.", "danger")
        
    return redirect(url_for("usuarios.listar_aptos_pendientes"))


@users_bp.route("/aptos/<int:id_apto>/rechazar", methods=["POST"])
@requiere_rol(['ADMINISTRADOR'])
def rechazar_apto(id_apto):
    """
    Ruta que se ejecuta al enviar el formulario de rechazo con su respectivo motivo.
    """
    # Capturamos el motivo del rechazo enviado desde el cuadro de texto (textarea)
    motivo = request.form.get("comentario")
    
    try:
        revisar_y_rechazar_apto(db.session, id_apto, motivo)
        flash("El apto físico ha sido rechazado y se notificará al cliente.", "info")
    except ValueError as e:
        # Si el administrador no escribió el comentario obligatorio, frena acá
        flash(str(e), "warning")
    except Exception as e:
        flash("Ocurrió un error inesperado al procesar el rechazo.", "danger")
        
    return redirect(url_for("usuarios.listar_aptos_pendientes"))

@users_bp.route('/perfil/editar', methods=['GET', 'POST'])
def editar_perfil():
    user_id = session.get('usuario_id')
    if not user_id:
        flash("Debes iniciar sesión para editar tu perfil.", "warning")
        return redirect(url_for('auth.login'))
    
    # Obtenemos el usuario de la base de datos
    usuario = db.session.get(Cliente, user_id)
    if not usuario:
        session.clear()
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # 1. Capturamos los datos del formulario eliminando espacios extras
        nuevo_nombre = request.form.get('nombre', '').strip()
        nuevo_telefono = request.form.get('telefono', '').strip()
        nueva_direccion = request.form.get('direccion', '').strip()
        
        if not nuevo_nombre:
            flash("El nombre completo es obligatorio.", "danger")
            dias_restantes = 0
            if usuario.apto_fisico and usuario.apto_fisico.estado and usuario.apto_fisico.estado.name == 'ACEPTADO':
                if hasattr(usuario.apto_fisico, 'fecha_carga') and usuario.apto_fisico.fecha_carga:
                    fecha_vencimiento = usuario.apto_fisico.fecha_carga + timedelta(days=365)
                    dias_restantes = (fecha_vencimiento - datetime.now()).days
            return render_template('usuarios/perfil.html', usuario=usuario, dias_restantes=dias_restantes, editando=True)
        
        # 2. Actualizamos el modelo permitiendo que queden vacíos (Guardamos None si es un string vacío)
        usuario.nombre = nuevo_nombre
        usuario.telefono = nuevo_telefono if nuevo_telefono else None
        usuario.direccion = nueva_direccion if nueva_direccion else None
        
        # 3. Impactamos la Base de Datos
        try:
            db.session.commit()
            flash("Perfil actualizado con éxito.", "success")
            return redirect(url_for('usuarios.perfil'))
        except Exception as e:
            db.session.rollback()
            flash("Ocurrió un error al guardar los cambios. Inténtalo de nuevo.", "danger")
            
            # === Validamos paso a paso que no sea None ===
            dias_restantes = 0
            if usuario.apto_fisico and usuario.apto_fisico.estado and usuario.apto_fisico.estado.name == 'ACEPTADO':
                if hasattr(usuario.apto_fisico, 'fecha_carga') and usuario.apto_fisico.fecha_carga:
                    fecha_vencimiento = usuario.apto_fisico.fecha_carga + timedelta(days=365)
                    dias_restantes = (fecha_vencimiento - datetime.now()).days
                    
            return render_template('usuarios/perfil.html', usuario=usuario, dias_restantes=dias_restantes, editando=True)
    
    # 4. Si entra por GET, calculamos los días del apto para el renderizado del formulario
    dias_restantes = 0
    
    # === 'if usuario.apto_fisico' antes de evaluar sus propiedades ===
    if usuario.apto_fisico and usuario.apto_fisico.estado and usuario.apto_fisico.estado.name == 'ACEPTADO':
        if hasattr(usuario.apto_fisico, 'fecha_carga') and usuario.apto_fisico.fecha_carga:
            fecha_vencimiento = usuario.apto_fisico.fecha_carga + timedelta(days=365)
            dias_restantes = (fecha_vencimiento - datetime.now()).days

    # Reutilizamos tu HTML pasándole el flag 'editando=True'
    return render_template('usuarios/perfil.html', usuario=usuario, dias_restantes=dias_restantes, editando=True)

@users_bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@requiere_rol(['ADMINISTRADOR'])
def editar_usuario_admin(id):
    # Buscamos al usuario para cargar sus datos actuales en el formulario
    usuario = obtener_usuario_por_id_core(id)
    if not usuario:
        flash("El usuario no existe o fue eliminado.", "danger")
        return redirect(url_for('usuarios.lista_usuarios'))

    if request.method == 'POST':
        # Capturamos los datos del formulario
        nombre = request.form.get('nombre')
        direccion = request.form.get('direccion')
        email = request.form.get('email')
        telefono = request.form.get('telefono')

        try:
            # Intentamos actualizar mediante el core
            modificar_usuario_core(
                usuario_id=id,
                nombre=nombre,
                direccion=direccion,
                email=email,
                telefono=telefono
            )
            # Escenario 2: Cambios guardados con éxito
            flash("Perfil actualizado con éxito", "success")
            return redirect(url_for('usuarios.detalle_usuario', id=id)) # Ajustá al nombre de tu ruta de detalle
            
        except ValueError as e:
            # Escenario 4: Captura el error de email duplicado y vuelve a renderizar con el error
            return render_template('usuarios/editar_usuario.html', usuario=usuario, error=str(e))

    # Escenario 1: Muestra el formulario con los cuadros de texto
    return render_template('usuarios/editar_usuario.html', usuario=usuario)