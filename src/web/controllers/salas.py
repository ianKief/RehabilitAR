from flask import Blueprint, render_template, request, flash, redirect, url_for
from src.core.salas import *
from src.core.auditoria import registrar_log, TipoAccion
from src.web.helpers.decorator import requiere_rol
 
bp = Blueprint("salas", __name__, url_prefix="/salas")

@bp.route("/")
@requiere_rol(["ADMINISTRADOR"])
def lista_salas():
    salas = listar_salas()
    return render_template("salas/lista_salas.html", salas=salas,current_path=request.path)

@bp.route("/nueva", methods=["GET", "POST"])
@requiere_rol(["ADMINISTRADOR"])
def nueva_sala():
    if request.method == "POST":
        datos = {
            "numero_puerta": request.form.get("numero_puerta"),
            "descripcion": request.form.get("descripcion"),
            "capacidad": request.form.get("capacidad")
        }
        try:
            crear_sala(**datos)
            registrar_log(TipoAccion.CREACION_SALA, detalles=datos)
            flash("Sala agregada exitosamente", "success")
            return redirect(url_for("salas.lista_salas"))
        except ValueError as e:
            flash(str(e), "danger") 
            if str(e) == "El número de puerta ya se encuentra registrado":
                datos = None
            return render_template("salas/nueva_sala.html", datos=datos)
            
    return render_template("salas/nueva_sala.html", datos=None)

@bp.route("/<int:id>")
@requiere_rol(["ADMINISTRADOR"])
def ver_sala(id):
    sala = obtener_sala(id)
    if not sala:
        flash("La sala solicitada no existe.", "danger")
        return redirect(url_for("salas.lista_salas"))
    
    # Obtenemos las clases asignadas a la sala para mostrar su cronograma (Escenario 2)
    clases_asignadas = obtener_clases_por_sala(id)
    
    return render_template("salas/ver_sala.html", sala=sala, clases=clases_asignadas)

@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@requiere_rol(["ADMINISTRADOR"])
def editar_sala(id):
    sala = obtener_sala(id)
    if not sala:
        flash("La sala que intentas editar no existe.", "danger")
        return redirect(url_for("salas.lista_salas"))
        
    if request.method == "POST":
        datos = {
            "numero_puerta": request.form.get("numero_puerta"),
            "descripcion": request.form.get("descripcion"),
            "capacidad": request.form.get("capacidad")
        }
        try:
            actualizar_sala(id, **datos)
            registrar_log(TipoAccion.MODIFICACION_SALA, id_entidad_objetivo=id, detalles=datos)
            flash("Sala actualizada con éxito", "success")
            return redirect(url_for("salas.lista_salas"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("salas/editar_sala.html", sala=sala, datos=datos)
            
    return render_template("salas/editar_sala.html", sala=sala, datos=None)

@bp.route("/<int:id>/eliminar")
@requiere_rol(["ADMINISTRADOR"])
def eliminar_sala_route(id):
    try:
        # Obtenemos la sala ANTES de eliminarla para registrar su número
        sala_a_eliminar = obtener_sala(id)
        if not sala_a_eliminar:
            flash("No se pudo eliminar la sala. Es posible que no exista.", "danger")
            return redirect(url_for("salas.lista_salas"))

        if eliminar_sala(id):
            registrar_log(TipoAccion.ELIMINACION_SALA, id_entidad_objetivo=id, detalles={'numero_puerta_eliminado': sala_a_eliminar.numero_puerta})
            flash("Sala eliminada con éxito.", "success")
        else:
            flash("No se pudo eliminar la sala. Es posible que no exista.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("salas.lista_salas"))

@bp.route("/<int:id>/toggle")
@requiere_rol(["ADMINISTRADOR"])
def toggle_estado_route(id):
    try:
        sala = toggle_estado_sala(id)
        registrar_log(TipoAccion.CAMBIO_ESTADO_SALA, id_entidad_objetivo=id, detalles={'nuevo_estado': sala.estado.name})
        if sala:
            if sala.estado.name == "HABILITADA":
                flash("Sala habilitada para nuevas clases", "success")
            else:
                flash("Sala deshabilitada correctamente", "success")
        else:
            flash("No se pudo actualizar el estado. La sala no existe.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("salas.lista_salas"))