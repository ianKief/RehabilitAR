def filtrarPorNombre (nombre, usuarios):
    texto = nombre.lower()

    return [
        usuario
        for usuario in usuarios
        if texto in usuario.nombre.lower() or texto in usuario.apellido.lower()
    ]