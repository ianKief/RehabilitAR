from flask_mail import Message
import threading

def enviar_email_asincrono(app, msg):
    from src.web import mail
    with app.app_context():
        mail.send(msg)

def enviar_correo(subject="Asunto", recipients=["destino@correo.com"], body="Contenido"):
    """Recipients recibe SOLO MAILS, uno o varios"""
    from flask import current_app
    print(type(current_app))
    print(current_app)
    # Esta comprobación se hace en las notificaciones, pero la dejo por si se llega a usar la función desde otra parte del sistema
    if isinstance(recipients, list):
        iterable = recipients
    else:
        iterable = [recipients]

    msg = Message(
        subject=subject,
        recipients=iterable,
        body=body,
        bcc=iterable # Esto sirve para que no se vean otros destinatarios
    )
        # Este sistema no está adaptado para enviar múltiples correos con contenido personalizado (por ejemplo, nombre del receptor). Esto es así porque no me pareció necesario hacerlo. Asumo que no se envía contenido que no sea texto
    threading.Thread(target=enviar_email_asincrono, args=(current_app._get_current_object(), msg)).start()
