// src/web/static/js/agenda-dinamica.js
function inicializarAgendaDinamica(apiUrl, diasNoLaborables) {
    document.addEventListener('DOMContentLoaded', function() {
        const fechaInput = document.getElementById('fecha_input');
        const duracionSelect = document.getElementById('duracion_select');
        const horarioSelect = document.getElementById('horario_select');
        const tipoClaseSelect = document.getElementById('tipo_clase_select');
        const salaSelect = document.getElementById('sala_select');
        
        // --- Configuración de Flatpickr ---
        const mañana = new Date();
        mañana.setDate(mañana.getDate() + 1);

        const fp = flatpickr(fechaInput, {
            locale: "es",
            dateFormat: "Y-m-d",
            minDate: mañana,
            disable: diasNoLaborables,
            onChange: function(selectedDates, dateStr, instance) {
                actualizarHorariosDisponibles();// Al cambiar la fecha, actualizamos los horarios de forma nativa.
            }
        });

        // Habilitación secuencial del formulario
        salaSelect.addEventListener('change', function() {
            if (this.value) {
                fechaInput.disabled = false;
            } else {
                fechaInput.disabled = true;
                fp.clear(); // Limpiamos la fecha si se deselecciona la sala
                horarioSelect.disabled = true;
                horarioSelect.innerHTML = '<option value="">Seleccione fecha, sala y duración primero...</option>';
            }
            actualizarHorariosDisponibles();
        });

        // Consulta al controlador los horarios libres mediante Fetch
        async function actualizarHorariosDisponibles() {
            const fecha = fechaInput.value;
            const duracion = duracionSelect.value;
            const sala = salaSelect.value; 
            const tipo = tipoClaseSelect.value; 

            if (!sala || !fecha) {
                horarioSelect.disabled = true;
                horarioSelect.innerHTML = '<option value="">Seleccione primero fecha y duración...</option>';
                return; 
            }

            horarioSelect.disabled = true;
            horarioSelect.innerHTML = '<option value="">Cargando horarios libres...</option>';

            try {
                // 🔄 Reemplazamos la llamada directa por el parámetro dinámico recibido
                const response = await fetch(`${apiUrl}?fecha=${fecha}&duracion=${duracion}&sala_id=${sala}&tipo=${tipo}`);
                const horariosLibres = await response.json();

                horarioSelect.innerHTML = ''; 

                if (horariosLibres.length === 0) {
                    horarioSelect.innerHTML = '<option value="">No hay horarios disponibles</option>';
                } else {
                    horariosLibres.forEach(hora => {
                        const option = document.createElement('option');
                        option.value = hora;
                        option.textContent = `${hora} hs`;
                        // 💡 Línea errónea eliminada
                        horarioSelect.appendChild(option); // Este es el único que necesitás
                    });
                    horarioSelect.disabled = false; 
                }
            } catch (error) {
                console.error("Error crítico de comunicación con la API del Core:", error);
                horarioSelect.innerHTML = '<option value="">Error al conectar con la agenda</option>';
            }
        }

        fechaInput.addEventListener('change', actualizarHorariosDisponibles);
        duracionSelect.addEventListener('change', actualizarHorariosDisponibles);
        salaSelect.addEventListener('change', actualizarHorariosDisponibles);
        tipoClaseSelect.addEventListener('change', actualizarHorariosDisponibles);
    });
}