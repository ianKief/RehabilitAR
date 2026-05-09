# RehabilitAR

Repositorio para el proyecto "RehabilitAR" de la materia Ingeniería de Software 2

## GRUPO 25

- Ian Kieferling
- Geronimo Basigalup
- Alfonso Armanini
- Elvis Valeiras
- Yuta Koyanagi

## Tecnologías utilizadas

- Python 3.13
- Flask (>=3.1.3,<4.0.0)
- Jinja2 (>=3.1.6,<4.0.0)
- Poetry (gestor de dependencias y entornos)

## Dependencias principales

- Flask
- Jinja2

## Dependencias de desarrollo

- pytest (tests)
- black (formateo de código)

## Configuración del ambiente para desarrolladores

1. Instala Poetry si no lo tienes:
	```bash
	pip install poetry
	```
2. Instala las dependencias del proyecto:
	```bash
	poetry install
	```
3. Activa el entorno virtual:
	```bash
	poetry shell
	```
4. Ejecuta la aplicación:
	```bash
	poetry run python main.py
	```

## Estructura del proyecto

- `src/web/static/`: Archivos estáticos (CSS, JS, imágenes)
- `src/web/templates/`: Plantillas HTML (Jinja2)
- `main.py`: Punto de entrada de la aplicación
- `tests/`: Pruebas

---
