from flask import Blueprint, render_template, request, flash
from src.web.helpers.decorator import requiere_rol
from src.core.auditoria import listar_logs, TipoAccion
from datetime import datetime, date, timedelta

bp = Blueprint("auditoria", __name__, url_prefix="/auditoria")

@bp.get("/logs")
@requiere_rol(['ADMINISTRADOR'])
def listar_logs_web():
    """Muestra el listado filtrable de logs de auditoría."""
    
    # Parámetros de filtro
    filtros = {
        'is_search': request.args.get('is_search', default=None, type=str),
        'tipo_accion': request.args.get('tipo_accion', default=None, type=str),
        'id_usuario_actor': request.args.get('id_usuario_actor', default=None, type=int),
        'fecha_desde_str': request.args.get('fecha_desde', default='', type=str),
        'fecha_hasta_str': request.args.get('fecha_hasta', default='', type=str),
        'rango_fecha': request.args.get('rango_fecha', default=None, type=str)
    }

    # Procesar rangos de fecha predefinidos
    hoy = date.today()
    if filtros['rango_fecha']:
        rango = filtros['rango_fecha']
        if rango == 'hoy':
            filtros['fecha_desde'] = hoy
            filtros['fecha_hasta'] = hoy
        elif rango == 'ayer':
            ayer = hoy - timedelta(days=1)
            filtros['fecha_desde'] = ayer
            filtros['fecha_hasta'] = ayer
        elif rango == '7dias':
            filtros['fecha_desde'] = hoy - timedelta(days=6)
            filtros['fecha_hasta'] = hoy
        elif rango == '30dias':
            filtros['fecha_desde'] = hoy - timedelta(days=29)
            filtros['fecha_hasta'] = hoy
        elif rango == 'mes_actual':
            filtros['fecha_desde'] = hoy.replace(day=1)
            filtros['fecha_hasta'] = hoy
        
        # Actualizar los strings de fecha para que los inputs muestren el rango
        if filtros.get('fecha_desde'):
            filtros['fecha_desde_str'] = filtros['fecha_desde'].strftime('%Y-%m-%d')
        if filtros.get('fecha_hasta'):
            filtros['fecha_hasta_str'] = filtros['fecha_hasta'].strftime('%Y-%m-%d')
    else:
        # Convertir fechas string a objetos datetime si no hay rango predefinido
        try:
            if filtros['fecha_desde_str']:
                filtros['fecha_desde'] = datetime.strptime(filtros['fecha_desde_str'], '%Y-%m-%d').date()
            else:
                filtros['fecha_desde'] = None
                
            if filtros['fecha_hasta_str']:
                filtros['fecha_hasta'] = datetime.strptime(filtros['fecha_hasta_str'], '%Y-%m-%d').date()
            else:
                filtros['fecha_hasta'] = None
        except ValueError:
            flash("Formato de fecha inválido. Use AAAA-MM-DD.", "danger")
            filtros['fecha_desde'] = None
            filtros['fecha_hasta'] = None
            filtros['fecha_desde_str'] = ''
            filtros['fecha_hasta_str'] = ''

    # Validaciones de fechas
    if filtros.get('fecha_desde') and filtros['fecha_desde'] > hoy:
        flash("La fecha 'Desde' no puede ser una fecha futura.", "danger")
        filtros['fecha_desde'] = None
        filtros['fecha_desde_str'] = ''

    if filtros.get('fecha_hasta') and filtros['fecha_hasta'] > hoy:
        flash("La fecha 'Hasta' no puede ser una fecha futura.", "danger")
        filtros['fecha_hasta'] = None
        filtros['fecha_hasta_str'] = ''
        
    if filtros.get('fecha_desde') and filtros.get('fecha_hasta') and filtros['fecha_desde'] > filtros['fecha_hasta']:
        flash("La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.", "danger")
        filtros['fecha_desde'] = None
        filtros['fecha_desde_str'] = ''
        filtros['fecha_hasta'] = None
        filtros['fecha_hasta_str'] = ''


    kwargs_core = {k: v for k, v in filtros.items() if v is not None and v != '' and not k.endswith('_str') and k != 'rango_fecha'}

    logs = listar_logs(**kwargs_core)
    
    tipos_accion_disponibles = [e for e in TipoAccion]

    return render_template(
        "auditorias/listar_logs.html",
        logs=logs,
        tipos_accion=tipos_accion_disponibles,
        filtros=filtros
    )