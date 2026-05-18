const dropdown = document.getElementById('dropdown-filters');
const triggerBtn = document.querySelector('#dropdown-filters .dropdown-trigger button');
const clearBtn = document.getElementById('btn-clear-filters'); 
const closeMobileBtn = document.getElementById('close-filters-mobile');
const form = document.getElementById('search-form');

// Abrir y cerrar dropdown al hacer click en el botón principal
triggerBtn.addEventListener('click', (e) => {
  e.preventDefault();
  dropdown.classList.toggle('is-active');
});

// Cerrar en celular con la "X"
closeMobileBtn.addEventListener('click', () => {
  dropdown.classList.remove('is-active');
});

// Cerrar si hacen click fuera del menú (Solo en computadoras)
document.addEventListener('click', (e) => {
  if (window.innerWidth > 768 && !dropdown.contains(e.target)) {
    dropdown.classList.remove('is-active');
  }
});

clearBtn.addEventListener("click", () => {
  window.location.href =
  "/profesor/ver_asistencias"
})

/*
// Lógica del botón Limpiar Filtros
clearBtn.addEventListener('click', () => {
  // 1. Resetear el campo de texto de búsqueda
  form.querySelector('input[name="search"]').value = '';
  
  // 2. Resetear el campo de fecha
  form.querySelector('input[name="fecha"]').value = '';
  
  // 3. Desmarcar el checkbox
  form.querySelector('input[name="solo_activos"]').checked = false;
  
  // 4. Resetear los radios a la primera opción por defecto
  const radios = form.querySelectorAll('input[name="categoria"]');
  radios.forEach((radio, index) => {
    radio.checked = (index === 0); // Marca solo el primero
  });
});

*/