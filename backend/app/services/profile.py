from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.perfil_estudiante import PerfilEstudiante

VALID_LEVELS = {"bajo", "intermedio", "alto"}
DEFAULT_LEVEL = "intermedio"

# El frontend usa nombres "amigables" para los modos. Aqui los mapeamos
# al vocabulario canonico que entiende el resto del backend y la extension.
ALIAS_TO_LEVEL = {
    "tranquilo": "bajo",
    "alerta": "intermedio",
    "absoluta": "alto",
}
LEVEL_TO_ALIAS = {v: k for k, v in ALIAS_TO_LEVEL.items()}


def normalize_level(value: str | None) -> str | None:
    """Convierte cualquier alias del frontend o valor canonico al canonico
    (bajo/intermedio/alto). Devuelve None si no se puede mapear."""
    if not value:
        return None
    v = value.strip().lower()
    if v in VALID_LEVELS:
        return v
    return ALIAS_TO_LEVEL.get(v)


async def get_or_create_profile(
    session: AsyncSession,
    user_id: int,
    initial_level: str | None = None,
) -> PerfilEstudiante:
    """Devuelve el perfil del estudiante, creándolo si no existe.

    El nivel por defecto es 'intermedio'. Si se pasa `initial_level` se usa
    ese valor sólo cuando el perfil aún no existe (no sobreescribe).
    """
    result = await session.execute(
        select(PerfilEstudiante).where(PerfilEstudiante.estudiante_id == user_id)
    )
    perfil = result.scalars().first()
    if perfil is None:
        nivel = initial_level if initial_level in VALID_LEVELS else DEFAULT_LEVEL
        perfil = PerfilEstudiante(estudiante_id=user_id, nivel_restriccion=nivel)
        session.add(perfil)
        await session.commit()
        await session.refresh(perfil)
    return perfil
