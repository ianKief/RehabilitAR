from sqlalchemy import select
from src.core.database import db
from src.core.salas.salas import Sala, EstadoSala
from datetime import date

def listar_salas():
    """Obtiene una lista de todas las salas."""
    stmt = select(Sala).filter_by(eliminada=False).order_by(Sala.numero_puerta)
    return db.session.execute(stmt).scalars().all()

def obtener_sala(id):
    """Obtiene una sala por su ID."""
    sala = db.session.get(Sala, id)
    if sala and not sala.eliminada:
        return sala
    return None

def listar_salas_habilitadas():
    """Retorna los objetos completos de las salas habilitadas (para sacar ID y Puerta en el HTML)."""
    query = select(Sala).filter(Sala.estado == EstadoSala.HABILITADA)
    return db.session.scalars(query).all()

def crear_sala(**kwargs):
    """Crea una nueva sala en la base de datos."""
    numero_puerta = kwargs.get("numero_puerta")
    descripcion = kwargs.get("descripcion")
    capacidad = kwargs.get("capacidad")

    if not numero_puerta or not str(numero_puerta).strip() or not capacidad or not str(capacidad).strip():
        raise ValueError("Por favor, complete todos los campos obligatorios")

    numero_puerta_str = str(numero_puerta).strip()

    try:
        cap_val = int(capacidad)
        if cap_val <= 0:
            raise ValueError("Los valores numéricos deben ser mayores a cero")
    except ValueError as e:
        if str(e) == "Los valores numéricos deben ser mayores a cero":
            raise e
        raise ValueError("La capacidad debe ser un número válido.")
        
    if numero_puerta_str.startswith("-") or (numero_puerta_str.isdigit() and int(numero_puerta_str) <= 0):
        raise ValueError("Los valores numéricos deben ser mayores a cero")

    # Escenario 2: Agregar sala fallida por sala existente
    if buscar_sala_por_numero(numero_puerta_str):
        raise ValueError("El número de puerta ya se encuentra registrado")

    kwargs["numero_puerta"] = numero_puerta_str
    nueva_sala = Sala(**kwargs)
    db.session.add(nueva_sala)
    db.session.commit()
    return nueva_sala

def actualizar_sala(id, **kwargs):
    """Actualiza los datos de una sala """
    sala = obtener_sala(id)
    if not sala:
        return None

    # Validar capacidad mínima y número de puerta no vacío
    capacidad = kwargs.get("capacidad")
    if capacidad is not None and int(capacidad) < 1:
        raise ValueError("Verifique los datos ingresados antes de guardar")
        
    numero_puerta = kwargs.get("numero_puerta")
    if numero_puerta is not None and not str(numero_puerta).strip():
        raise ValueError("Verifique los datos ingresados antes de guardar")

    # Si se intenta cambiar el número, validar que no choque con otro
    if numero_puerta and numero_puerta != sala.numero_puerta:
        if buscar_sala_por_numero(numero_puerta):
            raise ValueError("El número de puerta ya está asignado a otra sala")

    for key, value in kwargs.items():
        setattr(sala, key, value)
    db.session.commit()
    return sala

def eliminar_sala(id):
    """Elimina lógicamente una sala de la base de datos."""
    sala = obtener_sala(id)
    if sala:
        if tiene_clases_pendientes(id):
            raise ValueError("Acción bloqueada: la sala tiene actividades programadas")
        sala.eliminada = True
        db.session.commit()
        return True
    return False

def buscar_sala_por_numero(numero_puerta):
    """Busca una sala por su número de puerta único."""
    return db.session.execute(select(Sala).filter_by(numero_puerta=numero_puerta, eliminada=False)).scalar_one_or_none()

def obtener_clases_por_sala(id_sala):
    """Obtiene el cronograma de clases asignadas a una sala."""
    try:
        from src.core.clases.clases import Clase
        stmt = select(Clase).filter_by(sala_id=id_sala).order_by(Clase.fecha_clase, Clase.horario)
        return db.session.execute(stmt).scalars().all()
    except ImportError:
        return []

def tiene_clases_pendientes(id_sala):
    """Verifica si una sala tiene clases asignadas a futuro."""
    try:
        from src.core.clases.clases import Clase
        stmt = select(Clase).filter(Clase.sala_id == id_sala, Clase.fecha_clase >= date.today())
        return db.session.execute(stmt).first() is not None
    except ImportError:
        return False

def toggle_estado_sala(id):
    """Alterna el estado de una sala entre HABILITADA y DESHABILITADA."""
    sala = obtener_sala(id)
    if not sala:
        return None
        
    if sala.estado == EstadoSala.HABILITADA:
        if tiene_clases_pendientes(id):
            raise ValueError("No se puede deshabilitar: existen clases pendientes en esta sala")
        sala.estado = EstadoSala.DESHABILITADA
    else:
        sala.estado = EstadoSala.HABILITADA
        
    db.session.commit()
    return sala
