from dataclasses import dataclass
from flask import render_template

@dataclass
class HTTPError:
    codigo: int
    mensaje: str
    description: str

def not_found(e):
    error = HTTPError(
        codigo=404,
        mensaje="Página no encontrada",
        description="La página que intentas acceder no existe."
    )
    return render_template("errores/error.html", error=error), 404

def unauthorized(e):
    error = HTTPError(
        codigo=401,
        mensaje="No autorizado",
        description="Debes iniciar sesión para acceder a este recurso."
    )
    return render_template("errores/error.html", error=error), 401

def forbidden(e):
    error = HTTPError(
        codigo=403,
        mensaje="Acceso prohibido",
        description="No tienes los permisos necesarios para realizar esta acción."
    )
    return render_template("errores/error.html", error=error), 403

def internal_server_error(e):
    error = HTTPError(
        codigo=500,
        mensaje="Error interno del servidor",
        description="Ha ocurrido un error inesperado. Por favor, intenta más tarde."
    )
    return render_template("errores/error.html", error=error), 500
