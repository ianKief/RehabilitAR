from flask import Blueprint, render_template, request, session, flash, redirect, url_for, current_app
from datetime import datetime, date, timedelta
import json
import urllib.request
import os

from src.web.helpers.decorator import requiere_rol
from src.core.usuarios import obtener_usuario_por_id_core, EstadoUsuario, tiene_apto_fisico_valido
from src.core.pagos import estado_abono_usuario, obtener_precio_clase_actual, tiene_beneficios, TipoBeneficio, registrar_pago_con_credito
from src.core.clases import clase_tiene_lugar
from src.core.reservas.reservas import AsistenciaReserva, EstadoCola
from src.core.reservas import (
    listar_clases_disponibles_para_cliente, 
    obtener_fechas_con_clases,
    obtener_ids_clases_reservadas,
    obtener_reserva,
    reactivar_reserva,
    cancelar_reserva_core,
    crear_reserva,
    contar_reservas_fijas_semanales,
    verificar_limite_reservas_mensuales,
    obtener_clases_mensuales,
    obtener_clase_por_id,
    obtener_alternativas_semana_para_clase,
    obtener_reservas_cliente,
    obtener_profesor_de_clase,
    obtener_cupos_ocupados,
    obtener_ids_clases_encoladas,
    obtener_ids_clases_llenas_donde_el_cliente_no_tiene_reserva,
    obtener_colas_cliente,
    obtener_cola,
    cancelar_cola_core,
    reactivar_cola,
    crear_espera_en_cola,
    cliente_tiene_conflicto_horario
)

reservas_bp = Blueprint("reservas", __name__, url_prefix="/reservas")

# Caché en memoria para no saturar la API externa ni enlentecer la carga de la página
_CACHE_FERIADOS = {}

def _verificar_apto_fisico(cliente, fecha_clase = datetime.now(), message="Debe contar con un apto físico aceptado y vigente para reservar.") -> bool:
    """Helper para validar el apto físico del cliente de forma centralizada."""
    if not tiene_apto_fisico_valido(cliente, fecha_clase):
        flash(message, "warning")
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

def _obtener_url_base() -> str:
    return os.getenv("URL_NGROK", request.url_root).rstrip('/')

@reservas_bp.get("/")
@requiere_rol(["CLIENTE"])
def calendario_cliente():
    """Ruta que muestra el calendario interactivo de clases para el cliente."""
    usuario_id = session.get("usuario_id")
    usuario = obtener_usuario_por_id_core(usuario_id)
    abonado = estado_abono_usuario(usuario_id) == "activo"
    
    # El cliente debe estar "activo" para acceder.
    if usuario.estado != EstadoUsuario.ACTIVO:
        flash("Tu cuenta debe estar activa para acceder al calendario y realizar reservas.", "warning")
        return redirect(url_for("home"))

    hoy = date.today()
    fecha_str = request.args.get("fecha", default=hoy.strftime("%Y-%m-%d"))
    tipo = request.args.get("tipo")
    especialidad = request.args.get("especialidad")
    
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

    # Verificamos si el abonado ya tiene un bloque mensual para deshabilitar el botón
    tiene_bloque_mensual = verificar_limite_reservas_mensuales(usuario_id, None)

    fecha_formateada = fecha_seleccionada.strftime("%d/%m/%Y")
    
    return render_template("reservas/calendario_reservas.html", clases=clases, fecha_seleccionada=fecha_str, fecha_formateada=fecha_formateada, tipo_seleccionado=tipo, especialidad_seleccionada=especialidad, feriados=feriados, fechas_con_clases=fechas_con_clases, ids_clases_reservadas=ids_clases_reservadas, es_abonado=abonado, ids_clases_encoladas=ids_clases_encoladas, ids_clases_llenas_donde_el_cliente_no_tiene_reserva = ids_clases_llenas_donde_el_cliente_no_tiene_reserva, tiene_bloque_mensual=tiene_bloque_mensual)

@reservas_bp.post("/<int:id_clase>/reservar")
@requiere_rol(["CLIENTE"])
def reservar_clase(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)
    clase = obtener_clase_por_id(id_clase)
    if not clase:
        flash("La clase solicitada no existe.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))
    
    # Verificamos si el apto físico es válido para el momento de la clase
    if not _verificar_apto_fisico(cliente, fecha_clase=datetime.combine(clase.fecha_clase, datetime.min.time())):
        return redirect(url_for("reservas.calendario_cliente"))
    
    conflicto_horario = cliente_tiene_conflicto_horario (clase, usuario_id)
    if conflicto_horario:
        flash (f"El cliente ya tiene una clase en el mismo horario: {conflicto_horario}", "warning")
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
        # Esta situación es totalmente irrisoria y nunca va a suceder
        if clase.aviso_alta_demanda:
            flash("No se puede solicitar en la clase solicitada", "danger")
            return redirect(url_for("reservas.calendario_cliente"))
        else:
            return redirect(url_for("reservas.abonar_cola", id_clase=id_clase))
        
    if clase.tipo == "Fija":
        # Contamos cuántas clases fijas tiene el cliente en la semana
        cantidad_reservas_semanales = contar_reservas_fijas_semanales(usuario_id, clase.fecha_clase)
        
        if estado_abono_usuario(usuario_id) == "activo":
            if cantidad_reservas_semanales >= 2: # Ya tiene su clase del abono + 1 extra
                flash("Límite alcanzado: como abonado, solo podés reservar una clase fija extra por semana.", "warning")
                return redirect(url_for("reservas.calendario_cliente"))
            flash("Como abonado, podés reservar una clase fija extra esta semana. Deberás abonarla de forma individual.", "info")
            return redirect(url_for("reservas.abonar_clase_fija", id_clase=id_clase))

        # Si no es abonado, solo puede tener 1
        if estado_abono_usuario(usuario_id) != "activo" and cantidad_reservas_semanales >= 1:
            flash("Límite alcanzado: solo podés reservar una clase fija por semana.", "warning")
            return redirect(url_for("reservas.calendario_cliente"))

        return redirect(url_for("reservas.abonar_clase_fija", id_clase=id_clase))
    
    if clase.tipo == "Individual":
        return redirect(url_for("reservas.abonar_individual", id_clase=id_clase))

    crear_reserva(usuario_id, id_clase)
    
    flash("¡Lugar reservado con éxito!", "success")
    return redirect(url_for("reservas.calendario_cliente"))

@reservas_bp.route("/<int:id_clase>/abonar_fija", methods=["GET", "POST"])
@requiere_rol(["CLIENTE"])
def abonar_clase_fija(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)

    clase = obtener_clase_por_id(id_clase)
    if not clase:
        flash("La clase solicitada no existe.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    if clase.tipo != "Fija":
        flash("El pago de clase fija solo aplica a clases fijas.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))
    
    # Si el usuario NO es abonado, se mantiene el límite estricto de una clase por semana.
    # Si es abonado, se saltea esta validación porque se le permite pagar una clase extra.
    if estado_abono_usuario(usuario_id) != "activo" and contar_reservas_fijas_semanales(usuario_id, clase.fecha_clase) >= 1:
        flash("Límite alcanzado: solo puedes reservar una clase fija por semana.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))
        
    # Verificamos si el apto físico seguirá habilitado para el momento de la clase
    if not _verificar_apto_fisico(cliente, fecha_clase=datetime.combine(clase.fecha_clase, datetime.min.time())):
        return redirect(url_for("reservas.calendario_cliente"))

    if not clase_tiene_lugar(clase):
        flash("No hay lugares disponibles. Próximamente habilitaremos la opción de Inscribirse en lista de espera.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    precio = obtener_precio_clase_actual("Fija")

    if request.method == "POST":

        sdk = current_app.mp_sdk

        URL = _obtener_url_base()
        print(URL)

        preference_data = {
            "items": [{
                "title": f"Reserva Clase Fija: {clase.nombre}",
                "quantity": 1,
                "unit_price": float(precio)
            }],

            "external_reference": f"{usuario_id}:{id_clase}",

            "notification_url": (
                f"{URL}{url_for('pagos.webhook')}"
            ),

            "metadata": {
                "id_clase": id_clase,
                "tipo": "reserva_fija",
                "usuario_id": usuario_id
            },

            "back_urls": {
                "success": (
                    f"{URL}{url_for('pagos.pago_exitoso', tipo='reserva_fija')}"
                ),
                "failure": (
                    f"{URL}{url_for('pagos.pago_fallido', tipo='reserva_fija', id_clase=id_clase)}"
                ),
                "pending": (
                    f"{URL}{url_for('pagos.pago_pendiente', tipo='reserva_fija')}"
                )
            },

            "auto_return": "approved"
        }

        try:
            preference_response = sdk.preference().create(preference_data)
            if preference_response and preference_response.get("status") in [200, 201]:
                return redirect(preference_response["response"]["init_point"])
            else:
                print("Error de Mercado Pago (abonar_clase_fija):", preference_response)
                flash("Hubo un problema al comunicarse con Mercado Pago. Por favor, intentá de nuevo.", "danger")
                return redirect(url_for("reservas.abonar_clase_fija", id_clase=id_clase))
        except (KeyError, Exception) as e:
            print(f"Error al crear preferencia de pago para clase fija: {e}")
            flash("Ocurrió un error inesperado al procesar el pago. Por favor, contactá a soporte.", "danger")
            return redirect(url_for("reservas.calendario_cliente"))

    return render_template("pagos/pago_clase_fija.html", clase=clase, precio=precio)

@reservas_bp.route("/<int:id_clase>/abonar_cola", methods=["GET", "POST"])
@requiere_rol(["CLIENTE"])
def abonar_cola(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)

    clase = obtener_clase_por_id(id_clase)
    if not clase:
        flash("La clase solicitada no existe.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))
    
    if clase.aviso_alta_demanda:
        flash("No se puede solicitar en la clase solicitada", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    # Verificamos si el apto físico seguirá habilitado para el momento de la clase
    if not _verificar_apto_fisico(cliente, fecha_clase=datetime.combine(clase.fecha_clase, datetime.min.time())):
        return redirect(url_for("reservas.calendario_cliente"))

    # Verificamos si existía un espacio de la cola previo. En ese caso, reactivamos la cola nuevamente sin pasar por el costo
    # Verificamos también si tiene una reserva cancelada previa. En ese caso, activamos la cola nuevamente sin pasar por el costo
    cola = obtener_cola(usuario_id, clase.id)
    reserva = obtener_reserva(usuario_id, clase.id)
    if cola != None:
        if cola.estado == EstadoCola.EN_RESERVA:
            if reserva.asiste == AsistenciaReserva.CANCELADA:
                reactivar_cola (cola)
                flash ("Has perdido tu lugar en la clase porque se llenó. La previa acreditación es válida")
                # TODO dado cómo funciona esto, cuando alguien se dé de baja y dé espacio a otro, debería comprobarse que exista una reserva cancelada previamente, momento en el que pregunto ¿Qué hacemos? Deshacer la cancelación es borrarla de al estadística ¿Creamos otra cancelación?
            else:
                flash ("¡Ya tienes una reserva de esta clase en curso!", "success")
        elif cola.estado == EstadoCola.EN_CURSO:
            flash ("Usted ya tiene un espacio en la cola activo", "success")
        elif cola.estado == EstadoCola.CANCELADO:
            reactivar_cola (cola)
            flash ("Se ha reactivado su espacio en la cola")
        return redirect(url_for("reservas.calendario_cliente"))

    # Si tengo una reserva sin haber hecho una cola
    if reserva:
        if reserva.asiste == AsistenciaReserva.CANCELADA:
            crear_espera_en_cola (usuario_id, clase.id)
            flash ("Se ha creado un espacio en la cola. Se ha utilizado el pago de la reserva", "success")
        else:
            flash ("¡Ya tienes una reserva de esta clase en curso!", "success")
        return redirect(url_for("reservas.calendario_cliente"))



    precio = obtener_precio_clase_actual("Individual")

    if request.method == "POST":
        
        # --- TODO: IMPLEMENTACIÓN DE MERCADO PAGO ---
        # 2. Conectamos con Mercado Pago

        sdk = current_app.mp_sdk

        URL = _obtener_url_base()
        print(URL)

        preference_data = {
            "items": [{
                "title": f"Espera para clase: {clase.nombre}",
                "quantity": 1,
                "unit_price": float(precio)
            }],

            "external_reference": f"{usuario_id}:{id_clase}",

            "notification_url": (
                f"{URL}{url_for('pagos.webhook')}"
            ),

            "metadata": {
                "id_clase": id_clase,
                "tipo": "cola",
                "usuario_id": usuario_id
            },

            "back_urls": {
                "success": (f"{URL}{url_for('pagos.pago_exitoso', tipo='reserva_fija')}"),
                "failure": (f"{URL}{url_for('pagos.pago_fallido', tipo='reserva_fija', id_clase=id_clase)}"),
                "pending": (f"{URL}{url_for('pagos.pago_pendiente', tipo='reserva_fija')}")
            },

            "auto_return": "approved"
        }

        try:
            preference_response = sdk.preference().create(preference_data)
            if preference_response and preference_response.get("status") in [200, 201]:
                return redirect(preference_response["response"]["init_point"])
            else:
                print("Error de Mercado Pago (abonar_cola):", preference_response)
                flash("Hubo un problema al comunicarse con Mercado Pago. Por favor, intentá de nuevo.", "danger")
                return redirect(url_for("reservas.abonar_cola", id_clase=id_clase))
        except (KeyError, Exception) as e:
            print(f"Error al crear preferencia de pago para cola: {e}")
            flash("Ocurrió un error inesperado al procesar el pago. Por favor, contactá a soporte.", "danger")
            return redirect(url_for("reservas.calendario_cliente"))

    return render_template("pagos/pago_esperar_clase.html", clase=clase, precio=precio)

@reservas_bp.route("/<int:id_clase>/abonar_individual", methods=["GET", "POST"])
@requiere_rol(["CLIENTE"])
def abonar_individual(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)

    clase = obtener_clase_por_id(id_clase)
    if not clase:
        flash("La clase solicitada no existe.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    if clase.tipo != "Individual":
        flash("El pago de seña solo aplica a clases individuales.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))
        
    # Verificamos si el apto físico seguirá habilitado para el momento de la clase
    if not _verificar_apto_fisico(cliente, fecha_clase=datetime.combine(clase.fecha_clase, datetime.min.time())):
        return redirect(url_for("reservas.calendario_cliente"))

    if not clase_tiene_lugar(clase):
        flash("No hay lugares disponibles. Intente anotarse a la lista de espera.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    precio = obtener_precio_clase_actual("Individual")

    tiene_credito = tiene_beneficios (usuario_id, tipo=TipoBeneficio.CREDITO)

    if request.method == "GET":
        return render_template(
            "pagos/pago_senia.html",
            clase=clase,
            precio=precio,
            tiene_credito = tiene_credito
        )

    # =========================
    # POST
    # =========================
    porcentaje = request.form.get("porcentaje", type=int)
    credito = request.form.get("credito")

    # Si hay crédito, evitamos hacer pago por MP porque no se pueden hacer pagos de $0
    if credito != None:
        try:
            registrar_pago_con_credito (cliente, clase, precio)
        except ValueError as e:
            flash (str(e))
        flash ("Se ha usado el crédito con éxitos", "success")
        return redirect(url_for("reservas.calendario_cliente"))


    porcentajes_validos = [50, 60, 70, 80, 90, 100]
    
    if not credito and porcentaje not in porcentajes_validos:
        flash("Debes seleccionar un porcentaje válido (50% a 100%).", "danger")
        return redirect(url_for("reservas.abonar_individual", id_clase=id_clase))

    monto = (precio * porcentaje) / 100
    print ("El monto que mandé es", monto, "porque el porcenaje es", porcentaje)

    # =========================
    # MERCADO PAGO
    # =========================
    sdk = current_app.mp_sdk
    URL = _obtener_url_base()

    preference_data = {
        "items": [{
            "title": f"Clase Individual {clase.nombre} ({porcentaje}%)",
            "quantity": 1,
            "unit_price": float(monto)
        }],

        "external_reference": f"{usuario_id}:{id_clase}:{porcentaje}",

        "notification_url": (
            f"{URL}{url_for('pagos.webhook')}"
        ),

        "metadata": {
            "id_clase": id_clase,
            "tipo": "reserva_individual",
            "usuario_id": usuario_id,
            "porcentaje": porcentaje,
        },

        "back_urls": {
            "success": f"{URL}{url_for('pagos.pago_exitoso')}",
            "failure": f"{URL}{url_for('pagos.pago_fallido', tipo='reserva_individual', id_clase=id_clase)}",
            "pending": f"{URL}{url_for('pagos.pago_pendiente', tipo='reserva_individual')}"
        },

        "auto_return": "approved"
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        if preference_response and preference_response.get("status") in [200, 201]:
            return redirect(preference_response["response"]["init_point"])
        else:
            print("Error de Mercado Pago (abonar_individual):", preference_response)
            flash("Hubo un problema al comunicarse con Mercado Pago. Por favor, intentá de nuevo.", "danger")
            return redirect(url_for("reservas.abonar_individual", id_clase=id_clase))
    except (KeyError, Exception) as e:
        print(f"Error al crear preferencia de pago para clase individual: {e}")
        flash("Ocurrió un error inesperado al procesar el pago. Por favor, contactá a soporte.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

@reservas_bp.route("/<int:id_clase>/reservar_mensual", methods=["GET", "POST"])
@requiere_rol(["CLIENTE"])
def reservar_mensual(id_clase):
    usuario_id = session.get("usuario_id")
    cliente = obtener_usuario_por_id_core(usuario_id)

    clase_base = obtener_clase_por_id(id_clase)
    if not clase_base or clase_base.tipo != "Fija":
        flash("Clase no válida para reserva mensual.", "danger")
        return redirect(url_for("reservas.calendario_cliente"))

    # Verificamos si el apto físico seguirá habilitado para el momento de la clase
    if not _verificar_apto_fisico(cliente, fecha_clase=datetime.combine(clase_base.fecha_clase, datetime.min.time())):
        return redirect(url_for("reservas.calendario_cliente"))

    if verificar_limite_reservas_mensuales(usuario_id, clase_base):
        flash("Ya tenés un bloque de clases mensuales reservado para este mes.", "warning")
        return redirect(url_for("reservas.calendario_cliente"))

    feriados = _obtener_feriados(date.today().year)
    clases_mensuales = obtener_clases_mensuales(id_clase)
    
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
                alt for alt in alternativas_db if clase_tiene_lugar(alt) and alt.fecha_clase.strftime("%Y-%m-%d") not in feriados
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

@reservas_bp.post("/<int:id_clase>/confirmar-abono")
@requiere_rol(["CLIENTE"])
def confirmar_abono(id_clase):
    """
    Paso intermedio: recibe la selección de clases, calcula el precio
    y muestra la página de confirmación antes de pagar.
    """
    clases_seleccionadas_ids = request.form.getlist("clases_seleccionadas")

    if not clases_seleccionadas_ids:
        flash("No seleccionaste ninguna clase para reservar.", "warning")
        return redirect(url_for('reservas.reservar_mensual', id_clase=id_clase))

    # Calculamos el precio y lo pasamos a la plantilla de confirmación
    precio_clase_fija = obtener_precio_clase_actual("Fija")
    valor_abono = len(clases_seleccionadas_ids) * precio_clase_fija

    # Guardamos las clases seleccionadas en la sesión para el siguiente paso (pago)
    session['reserva_mensual_post_data'] = {'clases_seleccionadas': clases_seleccionadas_ids}

    clase_base = obtener_clase_por_id(id_clase)
    return render_template(
        "pagos/confirmar_abono_desde_reserva.html",
        clase_base=clase_base,
        valor_abono=valor_abono
    )

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
    capacidad_total = clase.sala.capacidad if clase.sala else 0
    cupos_restantes = max(0, capacidad_total - cupos_ocupados)
    
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
        flash(f"Error: {str(e)}", "warning")
        return redirect(url_for("reservas.mis_clases"))

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
        flash(f"Error: {str(e)}", "warning")
    
    return redirect(url_for("reservas.mis_clases"))