from flask_mail import Message
import threading
import time

def enviar_email_asincrono(app, msg):
    from src.web import mail
    with app.app_context():
        mail.send(msg)

def enviar_correo(subject="Asunto", recipients=["destino@correo.com"], body="Contenido"):
    """
    Recipients recibe SOLO MAILS, uno o varios.
    Modificado para enviar correos individualmente con un retardo para evitar rate-limiting.
    """
    from flask import current_app
    import time

    if not isinstance(recipients, list):
        recipients = [recipients]

    for recipient in recipients:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body
        )
        # Iniciar el envío en un hilo separado para no bloquear la aplicación
        threading.Thread(target=enviar_email_asincrono, args=(current_app._get_current_object(), msg)).start()
        # Esperar 1 segundo entre cada correo para no saturar el servidor SMTP
        time.sleep(1)
