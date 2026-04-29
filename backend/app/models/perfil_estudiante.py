from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from datetime import datetime
from .user import Base


class PerfilEstudiante(Base):
    __tablename__ = "perfiles_estudiante"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Relación 1:1 con users — cada estudiante tiene un único perfil
    estudiante_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    # Default 'intermedio' al crear cuenta; cambios no afectan sesión en curso
    nivel_restriccion = Column(
        Enum("bajo", "intermedio", "alto"),
        nullable=False,
        default="intermedio",
    )
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
