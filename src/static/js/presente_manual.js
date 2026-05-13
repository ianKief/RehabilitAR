document.getElementById("formulario").addEventListener("submit", enviarPresente)

async function enviarPresente (event) {
    event.preventDefault()

    const dni=document.getElementById("dni").value

    const response = await fetch("/profesor/presente_manual", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            dni: dni
        })
    })

    const data = await response.json()

    if (data.error) {
        document.getElementById("mensaje_error").style.display="block"
        document.getElementById("error").innerText = data.error
    }
}