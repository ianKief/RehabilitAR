from io import BytesIO
from flask import send_file
import qrcode, secrets
from flask import session, flash, redirect, url_for, abort
from src.core.database import db

from src.web.functions import devolver_enlace_absoluto_actual
from src.core.clases import obtener_clase_por_id, profesor_está_en_clase, conseguir_clase_actual

def mostrar_qr_en_pantalla(id_clase):
    clase = obtener_clase_por_id(id_clase)
    id_profesor = session.get("usuario_id")

    # Comprobación 1: el profesor está en una clase
    if not profesor_está_en_clase (id_profesor):
        flash ("El profesor no se encuentra en una clase", 'warning')
        return redirect(url_for("profesor.index_profesor"))

    # Comprobación 2: la clase que se está dictando es la puesta en la URL. Se muestra 404 para no comprometer información sensible
    clase_actual = conseguir_clase_actual(id_profesor)[0]
    if clase.id != clase_actual.id:
        abort(404)
    
    # Si no existe el QR, lo crea
    # Sinceramente, no sé si se puede generar 2 tokens iguales. Debería dar excepción en dicho caso porque token_qr es unique. Para esos casos prefiero que el profesor lo genere de vuelta para no hacer loops innecesarios. Al ser algo técnico, no lo voy a considerar para la HU.
    if clase.token_qr is None:
        try:
            clase.token_qr = (secrets.token_urlsafe(32))
            db.session.commit()
        except:
            flash ("Ha habido un error el enlace. Pruebe nuevamente")
            return redirect(url_for("Profesor.index_profesor"))
    url = (
        devolver_enlace_absoluto_actual()
        + url_for(
            "asistencia.registrar_asistencia_qr",
            token=clase.token_qr
        )
    )

    img = qrcode.make(url)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="image/png"
    )
    # TODO agregar una forma más linda de conseguir la imagen (devolverla en otra página, popup. Evaluar)