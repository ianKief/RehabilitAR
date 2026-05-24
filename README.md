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
- PostgreSQL 15 (Base de datos relacional)
- Bulma CSS (Framework de diseño)

## Dependencias principales

- Flask
- Jinja2
- python-dotenv
- psycopg2-binary
- flask-sqlalchemy-lite

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
	poetry run python app.py
	```

## Levantar la base de datos (via docker)

- Descarga e instala Docker Desktop desde su sitio oficial.
- Abre la aplicación Docker Desktop y asegúrate de que esté corriendo en segundo plano
- En la raíz del proyecto encontrarás un archivo llamado "docker-compose.yml". Para levantar la base de datos, abre tu terminal y ejecuta:
	```bash
	docker compose up -d
	```
- Para apagar los servicios cuando termines de trabajar:
	```Bash
	docker compose down
	```
- En el archivo "docker-compose.yml" van a estar las credenciales para poder conectarse a la bd y registrar en pgadmin
- En config.py estan las variables que tienes que tener en tu propio .env

### Cómo ingresar y conectar pgAdmin 4

- Una vez ejecutado el comando docker compose up -d, puedes gestionar la base de datos visualmente desde tu navegador.
- Abre tu navegador web e ingresa a: http://localhost:5050
- Inicia sesión con el correo y contraseña escrito en el archivo .yml.
- Para conectar pgAdmin con nuestra base de datos por primera vez:
- Haz clic derecho sobre Servers -> Register -> Server...
- En la pestaña General, asígnale un nombre (ej. RehabilitAR Local).
- En la pestaña Connection, completa los siguientes datos utilizando los valores de .yml:
  - Host name/address: db (Nota: Dentro de la red de Docker, se usa el nombre del servicio db, no localhost).
  - Port:
  - Maintenance database:
  - Username:
  - Password:
- Haz clic en Save.

### crear tablas y agregar datos de prueba

- `reset-db`: elimina todas las tablas y las vuelve a crear. si agregas tablas nuevas, debes importar la tabla en el siguiete codigo en database.py
	```python
	def reset_db():
    	from src.core.salas import Sala
    	`"""Reinicia la base de datos eliminando todas las tablas y volviéndolas a crear."""
    	print("Reiniciando la base de datos...")
    	Base.metadata.drop_all(bind=db.engine)
    	Base.metadata.create_all(bind=db.engine)
    	print("Base de datos reiniciada.")
	```
- `seed-db`: sirve para poblar con datos iniciales de prueba para interactuar con el sistema.
	```python
	def seed_db():
    	"""Pobla la base de datos con datos de prueba."""
    	from src.core.seeds.salas_seeds import SalaSeeder
    	seeder = SalaSeeder(db) 
    	seeder.run()
	```
- utiliza los siguientes comandos dentro del entorno de Poetry:
	```bash
	poetry run flask reset-db
	```
	```bash
	poetry run flask seed-db
	```

## Pasos para el uso de un gmail de prueba para enviar notificaciones

1. Crear una contraseña de aplicación en Gmail:
	- Debes tener activada la verificación en 2 pasos.
	- En el buscador de ajustes de tu cuenta busca "Contraseñas de aplicación"
	- Crea una nueva, te va a dar una contraseña de 16 letras (copiala)
2. Credenciales:
	- En tu archivo .env debes copiar esto:
		- MAIL_SERVER=smtp.gmail.com
		- MAIL_PORT=587
		- MAIL_USE_TLS=True
		- MAIL_USERNAME=tu_correo@gmail.com
		- MAIL_PASSWORD=las_16_letras_que_te_dio_google

## Arquitectura del Frontend: Bulma y Puntos de Extensión

El proyecto utiliza Bulma como framework CSS para el diseño visual, aprovechando clases utilitarias (is-primary, columns, button, etc.) para estructurar la interfaz de forma limpia y ágil.
Puntos de Extensión en layout.html
Para mantener la consistencia visual, todas las páginas del sistema deben heredar de src/web/templates/layout.html. Este archivo base define la estructura global (Navbar, Sidebar, Footer) y provee los siguientes bloques de Jinja2 ({% block %}) para que las vistas hijas inyecten su propio comportamiento:

- `title`: Define el título específico de la pestaña del navegador.

	```html
	{% block title %}Inicio - RehabilitAR{% endblock %}
	```

- `head_scripts`: Permite agregar hojas de estilo CSS adicionales o scripts específicos que deban cargarse en el `<head>`.
-  `content`: El bloque principal. Aquí va todo el cuerpo y componentes visuales de la vista actual (tablas, formularios, etc.).
-  
  ```html
  {% block content %}
  <section class="section">
      <div class="container">
          <h1 class="title">Bienvenido</h1>
      </div>
  </section>
  {% endblock %}
	```

## Estructura del proyecto

- `src/web/static/`: Archivos estáticos (CSS, JS, imágenes)
- `src/web/templates/`: Plantillas HTML (Jinja2)
- `app.py`: Punto de entrada de la aplicación
- `tests/`: Pruebas

---
