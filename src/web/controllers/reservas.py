from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from datetime import datetime, date
import json
import urllib.request

from src.web.helpers.decorator import requiere_rol
from src.core.usuarios import obtener_usuario_por_id_core, EstadoUsuario, tiene_apto_fisico_valido
from src.core.clases import clase_tiene_lugar
from src.core.reservas import (
    listar_clases_disponibles_para_cliente, 
    obtener_fechas_con_clases,
    obtener_ids_clases_reservadas,
    obtener_reserva,
    reactivar_reserva,
    crear_reserva,
    verificar_reserva_semanal_existente,
    obtener_clases_mensuales,
    procesar_reservas_mensuales_automatica,
    obtener_clase_por_id,
    cancelar_cola
)

reservas_bp = Blueprint("reservas", __name__, url_prefix="/reservas")

@reservas_bp.get("/")
@requiere_rol(["CLIENTE"])
def calendario_cliente():
    """Ruta que muestra el calendario interactivo de clases para el cliente."""
    usuario_id = session.get("usuario_id")
    usuario = obtener_usuario_por_id_core(usuario_id)
    es_abonado = getattr(usuario, 'es_abonado', False)
    
    # El cliente debe estar "activo" para acceder.
    if usuario.estado != EstadoUsuario.ACTIVO:
        flash("Tu cuenta debe estar activa para acceder al calendario y realizar reservas.", "warning")
        return redirect(url_for("home"))

    fecha_str = request.args.get("fecha")
    tipo = request.args.get("tipo")
    especialidad = request.args.get("especialidad")
    hoy = date.today()
    
    # Obtener feriados dinámicamente desde la API de ArgentinaDatos PRIMERO
    feriados = []
    try:
        url = f"https://api.argentinadatos.com/v1/feriados/{hoy.year}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            feriados = [item.get('fecha') for item in data if 'fecha' in item]
    except Exception as e:
        print(f"Advertencia: No se pudieron cargar los feriados de la API: {e}")
        feriados = [f"{hoy.year}-12-25", f"{hoy.year}-01-01"] # Fallback de emergencia

    if fecha_str:
        try:
            fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            # Bloqueo adicional por seguridad de URL
            if fecha_seleccionada < hoy:
                fecha_seleccionada = hoy
                fecha_str = hoy.strftime("%Y-%m-%d")
        except ValueError:
            fecha_seleccionada = hoy
            fecha_str = hoy.strftime("%Y-%m-%d")
    else:
        # Por defecto, selecciona el día de hoy
        fecha_seleccionada = hoy
        fecha_str = hoy.strftime("%Y-%m-%d")
        
    # Si hay filtros y el día elegido no tiene clases, saltamos al primer día disponible
    fechas_con_clases = obtener_fechas_con_clases(tipo=tipo, especialidad=especialidad)
    
    # Filtramos los feriados y fines de semana (Sábado=5, Domingo=6) para que no se puedan seleccionar
    fechas_con_clases = [
        f for f in fechas_con_clases 
        if f not in feriados and datetime.strptime(f, "%Y-%m-%d").date().weekday() < 5
    ]

    if fechas_con_clases and fecha_str not in fechas_con_clases:
        fecha_str = fechas_con_clases[0]
        fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()

    clases = listar_clases_disponibles_para_cliente(fecha=fecha_seleccionada, tipo=tipo, especialidad=especialidad)
    if fecha_str in feriados or fecha_seleccionada.weekday() >= 5:
        clases = []
    
    # Obtener las clases que el cliente ya tiene reservadas para deshabilitar los botones
    ids_clases_reservadas = []
    if usuario_id:
        ids_clases_reservadas = obtener_ids_clases_reservadas(usuario_id)

    fecha_formateada = fecha_seleccionada.strftime("%d/%m/%Y")
    
    return render_template("reservas/calendario_reservas.html", clases=clases, fecha_seleccionada=fecha_str, fecha_formateada=fecha_formateada, tipo_seleccionado=tipo, especialidad_seleccionada=especialidad, feriados=feriados, fechas_con_clases=fechas_con_clases, ids_clases_reservadas=ids_clases_reservadas, es_abonado=es_abonado)

@reservas_bp.post("/<int:id_clase>/reservar")
@requiere_rol(["CLIENTE"])
def reservar_clase(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)
    
    if not tiene_apto_fisico_valido(cliente):
        flash("Debe contar con un apto físico aceptado y vigente para reservar.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))
    
    reserva_existente = obtener_reserva(usuario_id, id_clase)
    if reserva_existente:
        if reserva_existente.asiste.name == 'CANCELADA':
            reactivar_reserva(reserva_existente)
            flash("¡Reserva reactivada exitosamente!", "success")
        else:
            flash("Ya tenés una reserva activa para esta clase.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))
    
    clase = obtener_clase_por_id(id_clase)
    if not clase:
        flash("La clase solicitada no existe.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))
        
    if not clase_tiene_lugar(clase):
        flash("No hay lugares disponibles. Próximamente habilitaremos la opción de Inscribirse en lista de espera.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))
        
    if clase.tipo == "Fija":
        if getattr(cliente, 'es_abonado', False):
            if verificar_reserva_semanal_existente(usuario_id, clase.fecha_clase):
                flash("Límite alcanzado: solo puede realizar una reserva puntual de clase fija por semana.", "warning")
                return redirect(url_for("reservas.calendario_cliente"))
        else:
            return redirect(url_for("reservas.abonar_clase", id_clase=id_clase))
    elif clase.tipo == "Individual":
        return redirect(url_for("reservas.abonar_clase", id_clase=id_clase))

    crear_reserva(usuario_id, id_clase)
    
    flash("¡Lugar reservado con éxito!", "success")
    return redirect(url_for("reservas.calendario_cliente"))

@reservas_bp.route("/<int:id_clase>/abonar", methods=["GET", "POST"])
@requiere_rol(["CLIENTE"])
def abonar_clase(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)

    if not tiene_apto_fisico_valido(cliente):
        flash("Debe contar con un apto físico aceptado y vigente para reservar.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))

    clase = obtener_clase_por_id(id_clase)
    if not clase:
        return redirect(url_for("reservas.calendario_cliente"))
        
    if not clase_tiene_lugar(clase):
        flash("No hay lugares disponibles. Próximamente habilitaremos la opción de Inscribirse en lista de espera.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    if request.method == "POST":
        crear_reserva(usuario_id, id_clase)
        
        flash("¡Pago de seña exitoso! Tu reserva para la clase individual ha sido confirmada.", "success")
        return redirect(url_for("reservas.calendario_cliente"))
        
    return render_template("reservas/pago_senia.html", clase=clase)

@reservas_bp.route("/<int:id_clase>/reservar_mensual", methods=["GET", "POST"])
@requiere_rol(["CLIENTE"])
def reservar_mensual(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)

    if not tiene_apto_fisico_valido(cliente):
        flash("Debe contar con un apto físico aceptado y vigente para reservar.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))

    clase_base = obtener_clase_por_id(id_clase)
    if not clase_base or clase_base.tipo != "Fija":
        flash("Clase no válida para reserva mensual.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    if not getattr(cliente, 'es_abonado', False):
        flash("Solo los clientes abonados pueden realizar reservas mensuales.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))

    hoy = date.today()
    feriados = []
    try:
        url = f"https://api.argentinadatos.com/v1/feriados/{hoy.year}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            feriados = [item.get('fecha') for item in data if 'fecha' in item]
    except Exception:
        pass

    clases_mensuales = obtener_clases_mensuales(id_clase)
    
    if request.method == "POST":
        clases_a_reservar = []
        for c in clases_mensuales:
            fecha_str = c.fecha_clase.strftime("%Y-%m-%d")
            
            reserva_exist = obtener_reserva(usuario_id, c.id)
            if reserva_exist and reserva_exist.asiste.name != 'CANCELADA':
                continue

            if fecha_str in feriados:
                flash(f"La clase del {fecha_str} cae feriado. Próximamente habilitaremos la reprogramación/compensación.", "info")
                continue
                
            if not clase_tiene_lugar(c):
                flash(f"No hay cupo para la clase del {fecha_str}. Debes reprogramar esta sesión semanal.", "warning")
                continue

            clases_a_reservar.append(c)

        reservas_creadas = procesar_reservas_mensuales_automatica(usuario_id, clases_a_reservar)

        if reservas_creadas > 0:
            flash(f"¡Se han generado {reservas_creadas} reservas para el mes de forma automática!", "success")
        return redirect(url_for("reservas.calendario_cliente"))

    # GET: Construir la pantalla de confirmación previa
    conflictos_cupo = []
    conflictos_feriado = []
    clases_ok = []

    for c in clases_mensuales:
        fecha_str = c.fecha_clase.strftime("%Y-%m-%d")
        if fecha_str in feriados:
            conflictos_feriado.append(c)
        elif not clase_tiene_lugar(c):
            conflictos_cupo.append(c)
        else:
            clases_ok.append(c)
            
    meses_espanol = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    dias_semana_espanol = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}

    return render_template("reservas/reserva_mensual.html", 
                           clase_base=clase_base, 
                           clases_ok=clases_ok, 
                           conflictos_cupo=conflictos_cupo, 
                           conflictos_feriado=conflictos_feriado,
                           mes_nombre=meses_espanol[clase_base.fecha_clase.month],
                           dia_nombre=dias_semana_espanol[clase_base.fecha_clase.weekday()])


@reservas_bp.post("/<int:id_clase>/salir_de_cola")
@requiere_rol(["CLIENTE"])
def salir_de_cola (id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)
    url = request.referrer

    try:
        exito = cancelar_cola (usuario_id, id_clase)

        if exito:
            flash ("Se ha cancelado la reserva exitosamente", "sucess")
            redirect(url)
    except ValueError as e:
        flash (("No se ha podido cancelar la reserva:", str(e)), "warning")
        redirect (url)
