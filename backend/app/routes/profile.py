from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ..auth import current_active_user
from ..db import get_async_session
from ..models.user import User
from ..schemas.profile import RestrictionProfileOut, RestrictionProfileUpdate
from ..services.profile import get_or_create_profile

router = APIRouter(prefix="/profile", tags=["profile"])

MAX_PHRASES = 20
MAX_PHRASE_LEN = 280


class MotivationPhrasesOut(BaseModel):
    phrases: List[str]


class MotivationPhrasesIn(BaseModel):
    phrases: List[str] = Field(default_factory=list)


@router.get("/restriction", response_model=RestrictionProfileOut)
async def get_restriction_profile(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    perfil = await get_or_create_profile(session, user.id)
    return perfil


@router.patch("/restriction", response_model=RestrictionProfileOut)
async def update_restriction_profile(
    payload: RestrictionProfileUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    perfil = await get_or_create_profile(session, user.id)
    perfil.nivel_restriccion = payload.nivel_restriccion
    perfil.updated_at = datetime.utcnow()
    session.add(perfil)
    await session.commit()
    await session.refresh(perfil)
    return perfil


# ---------------------------------------------------------------------------
# Frases de motivacion personalizadas (mostradas en blocked.html de la extension)
# Se guardan en User.profile_data["motivation_phrases"] como lista de strings.
# ---------------------------------------------------------------------------

@router.get("/motivation-phrases", response_model=MotivationPhrasesOut)
async def get_motivation_phrases(
    user: User = Depends(current_active_user),
):
    data = user.profile_data or {}
    phrases = data.get("motivation_phrases") or []
    if not isinstance(phrases, list):
        phrases = []
    return MotivationPhrasesOut(phrases=[str(p) for p in phrases])


@router.put("/motivation-phrases", response_model=MotivationPhrasesOut)
async def update_motivation_phrases(
    payload: MotivationPhrasesIn,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Sanitizar: trim, descartar vacios y duplicados, limitar tamano y cantidad.
    cleaned: List[str] = []
    seen = set()
    for raw in payload.phrases:
        if not isinstance(raw, str):
            continue
        text = raw.strip()
        if not text or text in seen:
            continue
        if len(text) > MAX_PHRASE_LEN:
            raise HTTPException(
                status_code=422,
                detail=f"Cada frase debe tener maximo {MAX_PHRASE_LEN} caracteres",
            )
        cleaned.append(text)
        seen.add(text)
        if len(cleaned) >= MAX_PHRASES:
            break

    data = dict(user.profile_data or {})
    data["motivation_phrases"] = cleaned
    user.profile_data = data
    flag_modified(user, "profile_data")
    session.add(user)
    await session.commit()
    return MotivationPhrasesOut(phrases=cleaned)
