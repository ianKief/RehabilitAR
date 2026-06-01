from functools import wraps
from flask import session, redirect, url_for, abort

def requiere_rol(roles_permitidos):
    """
    Decorador que bloquea el acceso si el usuario no tiene el rol adecuado.
    Recibe una lista de roles permitidos, ej: ['ADMIN', 'RECEPCIONISTA']
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Verificamos si el usuario inició sesión
            if 'usuario_id' not in session:
                return redirect(url_for('auth.login'))
            
            # 2. Verificamos si su rol está en la lista de permitidos
            rol_actual = session.get('rol')
            if rol_actual not in roles_permitidos:
                abort(403) 
                
            # Si pasa los controles, lo dejamos entrar a la ruta original
            return f(*args, **kwargs)
        return decorated_function
    return decorator