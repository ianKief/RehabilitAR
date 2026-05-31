from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from datetime import datetime, date, timedelta
import json
import urllib.request

from src.web.helpers.decorator import requiere_rol
from src.core.usuarios import obtener_usuario_por_id_core, EstadoUsuario, tiene_apto_fisico_valido, informar_alta_demanda, es_abonado
from src.core.clases import clase_tiene_lugar, comprobar_alta_demanda
from src.core.reservas.reservas import AsistenciaReserva
from src.core.reservas import (
    listar_clases_disponibles_para_cliente, 
    obtener_fechas_con_clases,
    obtener_ids_clases_reservadas,
    obtener_reserva,
    reactivar_reserva,
    cancelar_reserva_core,
    crear_reserva,
    verificar_reserva_semanal_existente,
    obtener_clases_mensuales,
    procesar_reservas_mensuales_automatica,
    obtener_clase_por_id,
    obtener_alternativas_semana_para_clase,
    obtener_reservas_cliente,
    obtener_profesor_de_clase,
    obtener_cupos_ocupados,
    obtener_ids_clases_encoladas,
    crear_espera_en_cola,
    obtener_ids_clases_llenas_donde_el_cliente_no_tiene_reserva,
    obtener_colas_cliente,
    obtener_cola,
    cancelar_cola_core
)

#TODO verificar si cuando un cliente se da de baja de una clase se le da acceso a la persona correcta

reservas_bp = Blueprint("reservas", __name__, url_prefix="/reservas")

# Caché en memoria para no saturar la API externa ni enlentecer la carga de la página
_CACHE_FERIADOS = {}

def _verificar_apto_fisico(cliente) -> bool:
    """Helper para validar el apto físico del cliente de forma centralizada."""
    if not tiene_apto_fisico_valido(cliente):
        flash("Debe contar con un apto físico aceptado y vigente para reservar.", "warning")
        return False
    return True

def _obtener_feriados(year: int) -> list:
    """Obtiene los feriados del año desde la API y los cachea en memoria para mejorar el rendimiento."""
    if year in _CACHE_FERIADOS:
        return _CACHE_FERIADOS[year]
    
    feriados = []
    try:
        url = f"https://api.argentinadatos.com/v1/feriados/{year}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            feriados = [item.get('fecha') for item in data if 'fecha' in item]
            _CACHE_FERIADOS[year] = feriados
    except Exception as e:
        print(f"Advertencia: No se pudieron cargar los feriados de la API: {e}")
        feriados = [f"{year}-12-25", f"{year}-01-01"] # Fallback de emergencia
    return feriados

@reservas_bp.get("/")
@requiere_rol(["CLIENTE"])
def calendario_cliente():
    """Ruta que muestra el calendario interactivo de clases para el cliente."""
    usuario_id = session.get("usuario_id")
    usuario = obtener_usuario_por_id_core(usuario_id)
    abonado = es_abonado(usuario_id)
    print ("Es abonado:", abonado)
    
    # El cliente debe estar "activo" para acceder.
    if usuario.estado != EstadoUsuario.ACTIVO:
        flash("Tu cuenta debe estar activa para acceder al calendario y realizar reservas.", "warning")
        return redirect(url_for("home"))

    fecha_str = request.args.get("fecha")
    tipo = request.args.get("tipo")
    especialidad = request.args.get("especialidad")
    hoy = date.today()
    
    feriados = _obtener_feriados(hoy.year)

    try:
        fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else hoy
        fecha_seleccionada = max(fecha_seleccionada, hoy) # Bloqueo seguridad URL (no permite fechas pasadas)
    except (ValueError, TypeError):
        fecha_seleccionada = hoy
        
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
        
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
    
    ids_clases_llenas_donde_el_cliente_no_tiene_reserva = []
    if usuario_id:
        ids_clases_llenas_donde_el_cliente_no_tiene_reserva = obtener_ids_clases_llenas_donde_el_cliente_no_tiene_reserva (usuario_id)
    
    # Obtener las clases que el cliente ya tiene reservadas para deshabilitar los botones
    ids_clases_reservadas = []
    if usuario_id:
        ids_clases_reservadas = obtener_ids_clases_reservadas(usuario_id)

    # Obtener las clases que el cliente ya tiene encoladas para deshabilitar los botones
    ids_clases_encoladas = []
    if usuario_id:
        ids_clases_encoladas = obtener_ids_clases_encoladas(usuario_id)

    fecha_formateada = fecha_seleccionada.strftime("%d/%m/%Y")
    
    return render_template("reservas/calendario_reservas.html", clases=clases, fecha_seleccionada=fecha_str, fecha_formateada=fecha_formateada, tipo_seleccionado=tipo, especialidad_seleccionada=especialidad, feriados=feriados, fechas_con_clases=fechas_con_clases, ids_clases_reservadas=ids_clases_reservadas, es_abonado=abonado, ids_clases_encoladas=ids_clases_encoladas, ids_clases_llenas_donde_el_cliente_no_tiene_reserva = ids_clases_llenas_donde_el_cliente_no_tiene_reserva)

@reservas_bp.post("/<int:id_clase>/reservar")
@requiere_rol(["CLIENTE"])
def reservar_clase(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)
    
    if not _verificar_apto_fisico(cliente):
        return redirect(url_for("reservas.calendario_cliente"))
    
    #TODO debería verificarse si el apto físico vence para el momento de la clase

    #TODO verificar si hay una clase en curso para ese momento ??? Si quieren y da el tiempo :P

    clase = obtener_clase_por_id(id_clase)
    print (clase, "CLASE")
    print (id_clase, "ID CLASE")
    if not clase:
        flash("La clase solicitada no existe.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))
    
    reserva_existente = obtener_reserva(usuario_id, id_clase)
    if reserva_existente and clase_tiene_lugar(clase):
        if reserva_existente.asiste == AsistenciaReserva.CANCELADA:
            reactivar_reserva(reserva_existente)
            flash("¡Reserva reactivada exitosamente!", "success")
        else:
            flash("Ya tenés una reserva activa para esta clase.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))
        
    if not clase_tiene_lugar(clase):
        crear_espera_en_cola (usuario_id, id_clase)
        flash("No hay lugares disponibles. Se le ha anotado en la lista de espera", "warning")
        if comprobar_alta_demanda (clase):
            informar_alta_demanda (clase)
        return redirect(url_for("reservas.calendario_cliente"))
        
    if clase.tipo == "Fija":
        if es_abonado(usuario_id):
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

    if not _verificar_apto_fisico(cliente):
        return redirect(url_for("reservas.calendario_cliente"))
    
    #TODO debería verificarse si el apto físico vence para el momento de la clase

    clase = obtener_clase_por_id(id_clase)
    if not clase:
        flash("La clase solicitada no existe.", "danger")
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

    if not _verificar_apto_fisico(cliente):
        return redirect(url_for("reservas.calendario_cliente"))

    clase_base = obtener_clase_por_id(id_clase)
    if not clase_base or clase_base.tipo != "Fija":
        flash("Clase no válida para reserva mensual.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    if not es_abonado(usuario_id):
        flash("Solo los clientes abonados pueden realizar reservas mensuales.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))

    hoy = date.today()
    feriados = _obtener_feriados(hoy.year)

    clases_mensuales = obtener_clases_mensuales(id_clase)
    
    if request.method == "POST":
        # NUEVO FLUJO INTERACTIVO: El template envía qué clases eligió finalmente el usuario
        clases_seleccionadas_ids = request.form.getlist("clases_seleccionadas")
        canceladas_con_descuento = int(request.form.get("canceladas_con_descuento", 0))

        if clases_seleccionadas_ids or canceladas_con_descuento > 0:
            clases_a_reservar = []
            for cid in clases_seleccionadas_ids:
                clase_elegida = obtener_clase_por_id(int(cid))
                if clase_elegida and clase_tiene_lugar(clase_elegida):
                    clases_a_reservar.append(clase_elegida)

            reservas_creadas = procesar_reservas_mensuales_automatica(usuario_id, clases_a_reservar)

            mensaje = f"¡Se reservaron {reservas_creadas} clases con éxito!"
            if canceladas_con_descuento > 0:
                mensaje += f" Se aplicará descuento en la cuota por {canceladas_con_descuento} clase(s) cancelada(s)."
            flash(mensaje, "success" if reservas_creadas > 0 else "info")
                
            return redirect(url_for("reservas.calendario_cliente"))

        # FALLBACK AUTOMÁTICO: Por si la vista aún no tiene el nuevo formulario
        clases_a_reservar = []
        for c in clases_mensuales:
            fecha_str = c.fecha_clase.strftime("%Y-%m-%d")
            
            reserva_exist = obtener_reserva(usuario_id, c.id)
            if reserva_exist and reserva_exist.asiste != AsistenciaReserva.CANCELADA:
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
            # Si la cantidad de clases a reservar es menor a las del mes, significa que hubo conflictos
            if len(clases_a_reservar) == len(clases_mensuales):
                flash(f"¡Se han generado {reservas_creadas} reservas para el mes de forma automática!", "success")
            else:
                flash(f"¡Se reservaron {reservas_creadas} clases con éxito! Se omitieron las fechas sin cupo o feriados.", "success")
                
        return redirect(url_for("reservas.calendario_cliente"))

    # GET: Construir la pantalla de confirmación previa
    conflictos_cupo = []
    conflictos_feriado = []
    clases_ok = []
    alternativas_conflictos = {}

    for c in clases_mensuales:
        fecha_str = c.fecha_clase.strftime("%Y-%m-%d")
        if fecha_str in feriados or not clase_tiene_lugar(c):
            if fecha_str in feriados:
                conflictos_feriado.append(c)
            else:
                conflictos_cupo.append(c)
                
            alternativas_db = obtener_alternativas_semana_para_clase(c)
            alternativas_conflictos[c.id] = [
                alt for alt in alternativas_db 
                if clase_tiene_lugar(alt) and alt.fecha_clase.strftime("%Y-%m-%d") not in feriados
            ]
        else:
            clases_ok.append(c)
            
    meses_espanol = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    dias_semana_espanol = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}

    return render_template("reservas/reserva_mensual.html", 
                           clase_base=clase_base, 
                           clases_ok=clases_ok, 
                           conflictos_cupo=conflictos_cupo, 
                           conflictos_feriado=conflictos_feriado,
                           alternativas_conflictos=alternativas_conflictos,
                           mes_nombre=meses_espanol[clase_base.fecha_clase.month],
                           dia_nombre=dias_semana_espanol[clase_base.fecha_clase.weekday()])

@reservas_bp.get("/mis-clases")
@requiere_rol(["CLIENTE"])
def mis_clases():
    """Ruta que muestra el listado de clases reservadas del cliente."""
    usuario_id = session.get("usuario_id")
    usuario = obtener_usuario_por_id_core(usuario_id)
    
    if usuario.estado != EstadoUsuario.ACTIVO:
        flash("Tu cuenta debe estar activa para acceder a tus reservas.", "warning")
        return redirect(url_for("home"))
        
    reservas = obtener_reservas_cliente(usuario_id)
    colas = obtener_colas_cliente(usuario_id)
    hoy = date.today()

    reservas_futuras = [r for r in reservas if r.clase.fecha_clase >= hoy]
    reservas_pasadas = [r for r in reservas if r.clase.fecha_clase < hoy]
    reservas_pasadas.reverse()  # Ordenamos el historial de lo más reciente a lo más antiguo

    colas_futuras = [c for c in colas if c.clase.fecha_clase >= hoy]

    return render_template("reservas/mis_clases.html", reservas_futuras=reservas_futuras, reservas_pasadas=reservas_pasadas, colas_futuras=colas_futuras, hoy=hoy)

@reservas_bp.get("/<int:id_clase>/detalle")
@requiere_rol(["CLIENTE"])
def detalle_clase(id_clase):
    usuario_id = session.get("usuario_id")
    clase = obtener_clase_por_id(id_clase)
    if not clase:
        flash("La clase solicitada no existe.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))
        
    profesor = obtener_profesor_de_clase(id_clase)
    cupos_ocupados = obtener_cupos_ocupados(id_clase)
    cupos_restantes = max(0, clase.capacidad_maxima - cupos_ocupados)
    
    reserva = obtener_reserva(usuario_id, id_clase)
    cola = obtener_cola(usuario_id, id_clase)
    hoy = date.today()
    
    next_url = request.args.get("next")
    if not next_url:
        next_url = request.referrer if request.referrer else url_for("reservas.calendario_cliente")
        if request.path in next_url:
            next_url = url_for("reservas.calendario_cliente")
            
    return render_template(
        "reservas/detalle_clase.html",
        clase=clase, profesor=profesor, cupos_restantes=cupos_restantes,
        reserva=reserva, hoy=hoy, next_url=next_url, cola=cola
    )

@reservas_bp.post("/<int:id_clase>/cancelar")
@requiere_rol(["CLIENTE"])
def cancelar_reserva(id_clase):
    usuario_id = session.get("usuario_id")
    clase = obtener_clase_por_id(id_clase)
    reserva = obtener_reserva(usuario_id, id_clase)

    if not clase or not reserva or reserva.asiste == AsistenciaReserva.CANCELADA:
        flash("La reserva no existe o ya fue cancelada.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    # Combinamos fecha y hora para saber exactamente cuándo empieza la clase
    fecha_hora_clase = datetime.combine(clase.fecha_clase, clase.horario)
    ahora = datetime.now()

    # Cancelación fallida por clase ya comenzada
    if fecha_hora_clase <= ahora:
        flash("No es posible cancelar clases que ya han comenzado.", "danger")
        return redirect(url_for("reservas.detalle_clase", id_clase=id_clase))

    try:
        # Cancelamos la reserva, liberando el cupo inmediatamente
        cancelar_reserva_core(reserva)
        tiempo_restante = fecha_hora_clase - ahora
    except ValueError as e:
        flash (("Error:", str(e)), "warning")

    if clase.tipo == "Fija":
        # Lógicas de la HU "Dar de baja clase fija reservada"
        if tiempo_restante >= timedelta(hours=48):
            # TODO: su función aquí -> otorgar_credito_clase_fija(reserva.id)
            flash("Reserva cancelada con éxito. Se te ha otorgado un crédito por sesión completa.", "success")
        elif tiempo_restante >= timedelta(hours=24):
            # TODO: su función aquí -> aplicar_descuento_20_clase_fija(reserva.id)
            flash("Reserva cancelada con éxito. Se te ha otorgado un descuento del 20% en tu próxima liquidación.", "success")
        else:
            # TODO: insertar su función aquí -> registrar_perdida_turno_clase_fija(reserva.id)
            flash("Reserva cancelada. Al realizarse con menos de 24 horas de anticipación, el turno se considera perdido sin derecho a beneficio.", "warning")
            
    elif clase.tipo == "Individual":
        # Lógicas de la HU "Dar de baja clase individual reservada"
        if tiempo_restante >= timedelta(hours=24):
            # TODO: insertar su función aquí -> generar_reembolso(reserva.id)
            flash("Reserva cancelada con éxito. Se ha notificado al sistema para el reembolso total de tu seña.", "success")
        else:
            # TODO: insertar su función aquí -> registrar_perdida_sena(reserva.id)
            flash("Reserva cancelada. Al realizarse con menos de 24 horas de anticipación, la seña se ha perdido.", "warning")

    return redirect(url_for("reservas.mis_clases"))

@reservas_bp.post("/<int:id_clase>/salir_de_cola")
@requiere_rol(["CLIENTE"])
def salir_de_cola (id_clase):
    usuario_id = session.get("usuario_id")
    cola = obtener_cola(usuario_id, id_clase)
    
    try:
        cancelar_cola_core(cola)
    except ValueError as e:
        flash (("Error:", str(e)), "warning")
    
    return redirect(url_for("reservas.mis_clases"))