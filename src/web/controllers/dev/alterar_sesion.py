from flask import render_template, session, request

def alterar_sesion_manual ():
    if request.method == "POST":

        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        dni = request.form.get("dni")
        rol = request.form.get("rol")

        session["nombre"] = nombre
        session["apellido"] = apellido
        session["dni"] = dni
        session["rol"] = rol

        print (session.get("rol"))

        return render_template('index.html')

    elif request.method == "GET":
        return render_template ('dev/alterar_sesion.html')