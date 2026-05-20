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