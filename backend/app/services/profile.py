from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.perfil_estudiante import PerfilEstudiante

VALID_LEVELS = {"bajo", "intermedio", "alto"}
DEFAULT_LEVEL = "intermedio"


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
