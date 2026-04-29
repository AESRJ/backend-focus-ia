from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_active_user
from ..db import get_async_session
from ..models.user import User
from ..schemas.profile import RestrictionProfileOut, RestrictionProfileUpdate
from ..services.profile import get_or_create_profile

router = APIRouter(prefix="/profile", tags=["profile"])


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
