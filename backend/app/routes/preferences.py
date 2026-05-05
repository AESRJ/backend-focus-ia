from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ..auth import current_active_user
from ..db import get_async_session
from ..models.sesion import Sesion
from ..models.user import User
from ..schemas.preferences import PreferenceIn, PreferenceOut
from ..services.profile import VALID_LEVELS, get_or_create_profile

router = APIRouter(prefix="/preferences", tags=["preferences"])

DEFAULT_DURATION = 25


def _read_duration(user: User) -> int:
    data = user.profile_data or {}
    return int(data.get("duration", DEFAULT_DURATION))


@router.get("", response_model=PreferenceOut)
async def get_preferences(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Lee `mode` desde PerfilEstudiante (fuente de verdad) y `duration`
    desde User.profile_data."""
    perfil = await get_or_create_profile(session, user.id)
    return PreferenceOut(mode=perfil.nivel_restriccion, duration=_read_duration(user))


@router.post("", response_model=PreferenceOut)
async def save_preferences(
    payload: PreferenceIn,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Guarda `mode` en PerfilEstudiante y `duration` en User.profile_data."""
    perfil = await get_or_create_profile(session, user.id)

    # Sólo persistimos `mode` en perfil si es un nivel válido; en caso contrario
    # mantenemos el actual y aceptamos cualquier string como modo libre en JSON.
    if payload.mode in VALID_LEVELS:
        perfil.nivel_restriccion = payload.mode
        perfil.updated_at = datetime.utcnow()
        session.add(perfil)
        # Si hay una sesion activa, sincronizar su snapshot para que las
        # detecciones registradas a partir de ahora usen el nuevo nivel.
        activa = (
            await session.execute(
                select(Sesion).where(
                    Sesion.estudiante_id == user.id,
                    Sesion.estado == "activa",
                )
            )
        ).scalars().first()
        if activa is not None:
            activa.nivel_restriccion_sesion = payload.mode
            session.add(activa)
    else:
        # Modo no es uno de los niveles oficiales; lo guardamos en JSON
        # para no perder configuraciones futuras como "tranquilo", "intenso", etc.
        data = dict(user.profile_data or {})
        data["mode_alias"] = payload.mode
        user.profile_data = data
        flag_modified(user, "profile_data")
        session.add(user)

    # Duration siempre va en JSON
    data = dict(user.profile_data or {})
    data["duration"] = payload.duration
    user.profile_data = data
    flag_modified(user, "profile_data")
    session.add(user)

    await session.commit()
    await session.refresh(user)
    await session.refresh(perfil)

    # Devolvemos el modo efectivo (perfil) o el alias si se aceptó libre
    effective_mode = (
        perfil.nivel_restriccion
        if payload.mode in VALID_LEVELS
        else (user.profile_data or {}).get("mode_alias", perfil.nivel_restriccion)
    )
    return PreferenceOut(mode=effective_mode, duration=payload.duration)
