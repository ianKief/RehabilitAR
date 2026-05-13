/*
document
    .getElementById("limpiar")
    .addEventListener("click", () => {

        document
            .getElementById("busqueda")
            .value = ""
    })
*/

const buscador = document.getElementById("buscador")

const limpiar = document.getElementById("limpiar")

const form = document.getElementById("form-busqueda")

limpiar.addEventListener("click", () => {

    window.location.href =
        "/profesor/listado_alumnos"
})