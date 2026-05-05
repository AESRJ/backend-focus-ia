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
from ..services.profile import (
    LEVEL_TO_ALIAS,
    VALID_LEVELS,
    get_or_create_profile,
    normalize_level,
)

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
    desde User.profile_data. Devuelve el alias del frontend si se conoce."""
    perfil = await get_or_create_profile(session, user.id)
    alias = (user.profile_data or {}).get("mode_alias")
    mode = alias or LEVEL_TO_ALIAS.get(perfil.nivel_restriccion, perfil.nivel_restriccion)
    return PreferenceOut(mode=mode, duration=_read_duration(user))


@router.post("", response_model=PreferenceOut)
async def save_preferences(
    payload: PreferenceIn,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Guarda `mode` en PerfilEstudiante y `duration` en User.profile_data.

    Acepta tanto los niveles canonicos (bajo/intermedio/alto) como los alias
    del frontend (tranquilo/alerta/absoluta) y los normaliza al canonico.
    """
    perfil = await get_or_create_profile(session, user.id)

    nivel_canonico = normalize_level(payload.mode)

    if nivel_canonico is not None:
        perfil.nivel_restriccion = nivel_canonico
        perfil.updated_at = datetime.utcnow()
        session.add(perfil)
        # Recordar el alias original que envio el frontend para devolverlo en
        # GET y que la UI marque el boton correcto.
        data = dict(user.profile_data or {})
        data["mode_alias"] = payload.mode
        user.profile_data = data
        flag_modified(user, "profile_data")
        session.add(user)
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
            activa.nivel_restriccion_sesion = nivel_canonico
            session.add(activa)
    else:
        # Modo no mapea a ningun nivel oficial; lo guardamos solo como alias
        # libre en JSON sin tocar perfil.nivel_restriccion.
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

    # Devolvemos el alias si lo conocemos (asi la UI marca el boton correcto),
    # si no, devolvemos el nivel canonico almacenado.
    effective_mode = (user.profile_data or {}).get("mode_alias") or perfil.nivel_restriccion
    return PreferenceOut(mode=effective_mode, duration=payload.duration)
