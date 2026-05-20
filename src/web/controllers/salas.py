from flask import Blueprint, render_template, request, flash, redirect, url_for
from src.core.salas import listar_salas, crear_sala, obtener_sala, actualizar_sala, eliminar_sala, toggle_estado_sala
 
bp = Blueprint("salas", __name__, url_prefix="/salas")

@bp.route("/")
def lista_salas():
    salas = listar_salas()
    return render_template("salas/lista_salas.html", salas=salas,current_path=request.path)

@bp.route("/nueva", methods=["GET", "POST"])
def nueva_sala():
    if request.method == "POST":
        datos = {
            "numero_puerta": request.form.get("numero_puerta"),
            "descripcion": request.form.get("descripcion"),
            "capacidad": request.form.get("capacidad")
        }
        try:
            crear_sala(**datos)
            flash("Sala agregada exitosamente", "success")
            return redirect(url_for("salas.lista_salas"))
        except ValueError as e:
            flash(str(e), "danger") 
            if str(e) == "El nro de puerta ya se encuentra registrado":
                datos = None
            return render_template("salas/nueva_sala.html", datos=datos)
            
    return render_template("salas/nueva_sala.html", datos=None)

@bp.route("/<int:id>")
def ver_sala(id):
    sala = obtener_sala(id)
    if not sala:
        flash("La sala solicitada no existe.", "danger")
        return redirect(url_for("salas.lista_salas"))
    
    # Preparamos la estructura para el Escenario 2 (Cronograma)
    # Por ahora pasamos una lista vacía hasta integrar el modelo de Clases.
    clases_asignadas = []
    
    return render_template("salas/ver_sala.html", sala=sala, clases=clases_asignadas)

@bp.route("/<int:id>/editar", methods=["GET", "POST"])
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
            flash("Sala actualizada con éxito", "success")
            return redirect(url_for("salas.lista_salas"))
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("salas/editar_sala.html", sala=sala, datos=datos)
            
    return render_template("salas/editar_sala.html", sala=sala, datos=None)

@bp.route("/<int:id>/eliminar")
def eliminar_sala_route(id):
    try:
        if eliminar_sala(id):
            flash("Sala eliminada con éxito.", "success")
        else:
            flash("No se pudo eliminar la sala. Es posible que no exista.", "danger")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("salas.lista_salas"))

@bp.route("/<int:id>/toggle")
def toggle_estado_route(id):
    try:
        sala = toggle_estado_sala(id)
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