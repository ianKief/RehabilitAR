from sqlalchemy import ForeignKey, String

from src.core.usuarios.usuarios import Usuario
from src.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Especialidad(Base):
    __tablename__ = "especialidades"
    id: Mapped[int]= mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)  # Ej: "Tren Inferior", "Cardio"

class Profesor(Base):
    __tablename__ = "profesores"
    
    # Clave primaria que a su vez es clave foránea apuntando a Usuarios
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), primary_key=True)
    especialidad_id: Mapped[int] = mapped_column(ForeignKey("especialidades.id"), nullable=False)
    
    # Relaciones para navegar fácilmente desde el código
    usuario: Mapped["Usuario"] = relationship("Usuario")
    especialidad: Mapped["Especialidad"] = relationship("Especialidad")