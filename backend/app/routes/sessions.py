from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_active_user
from ..db import get_async_session
from ..models.registro_deteccion import RegistroDeteccion
from ..models.sesion import Sesion
from ..models.user import User
from ..schemas.sessions import SessionHistoryItem, SessionOut, SessionStartIn
from ..services.profile import get_or_create_profile

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _to_out(s: Sesion) -> SessionOut:
    # Fallback a 'intermedio' para sesiones legacy en BD donde la columna
    # quedo NULL (la tabla se creo cuando aun era nullable). El modelo actual
    # ya es NOT NULL, asi que solo cubre datos viejos.
    return SessionOut(
        id=s.id,
        start_time=s.fecha_inicio,
        end_time=s.fecha_fin,
        nivel_restriccion_sesion=s.nivel_restriccion_sesion or "intermedio",
    )


@router.get("/active", response_model=Optional[SessionOut])
async def get_active_session(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Sesion).where(
            Sesion.estudiante_id == user.id,
            Sesion.estado == "activa",
        )
    )
    sesion = result.scalars().first()
    if sesion is None:
        return None
    # Devolver el nivel ACTUAL del perfil (no el snapshot) para que los cambios
    # de preferencias se reflejen en vivo en la extension sin reiniciar sesion.
    # El snapshot en Sesion.nivel_restriccion_sesion se mantiene para historicos
    # y para los registros de deteccion (RegistroDeteccion.nivel_restriccion_activo).
    perfil = await get_or_create_profile(session, user.id)
    nivel_vivo = perfil.nivel_restriccion or sesion.nivel_restriccion_sesion or "intermedio"
    return SessionOut(
        id=sesion.id,
        start_time=sesion.fecha_inicio,
        end_time=sesion.fecha_fin,
        nivel_restriccion_sesion=nivel_vivo,
    )


@router.get("/history", response_model=List[SessionHistoryItem])
async def get_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Histórico de sesiones del usuario, ordenado por más reciente primero,
    con conteo de detecciones y duración en segundos."""
    detection_count = (
        select(
            RegistroDeteccion.sesion_id.label("sid"),
            func.count(RegistroDeteccion.id).label("total"),
        )
        .group_by(RegistroDeteccion.sesion_id)
        .subquery()
    )

    stmt = (
        select(Sesion, func.coalesce(detection_count.c.total, 0))
        .outerjoin(detection_count, detection_count.c.sid == Sesion.id)
        .where(Sesion.estudiante_id == user.id)
        .order_by(Sesion.fecha_inicio.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)

    items: List[SessionHistoryItem] = []
    for sesion, total in result.all():
        duracion = None
        if sesion.fecha_fin is not None:
            duracion = int((sesion.fecha_fin - sesion.fecha_inicio).total_seconds())
        items.append(
            SessionHistoryItem(
                id=sesion.id,
                start_time=sesion.fecha_inicio,
                end_time=sesion.fecha_fin,
                estado=sesion.estado,
                nivel_restriccion_sesion=sesion.nivel_restriccion_sesion,
                detecciones=int(total),
                duracion_segundos=duracion,
            )
        )
    return items


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: SessionStartIn = SessionStartIn(),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    # Reutilizar sesión activa si ya existe
    existing = await session.execute(
        select(Sesion).where(
            Sesion.estudiante_id == user.id,
            Sesion.estado == "activa",
        )
    )
    activa = existing.scalars().first()
    if activa is not None:
        return _to_out(activa)

    perfil = await get_or_create_profile(session, user.id)
    # Si el perfil legacy tiene nivel NULL, caemos al default oficial.
    sesion = Sesion(
        estudiante_id=user.id,
        nivel_restriccion_sesion=perfil.nivel_restriccion or "intermedio",
    )
    session.add(sesion)
    await session.commit()
    await session.refresh(sesion)
    return _to_out(sesion)


@router.patch("/{session_id}", response_model=SessionOut)
async def end_session(
    session_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Sesion).where(
            Sesion.id == session_id,
            Sesion.estudiante_id == user.id,
        )
    )
    sesion = result.scalars().first()
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if sesion.estado == "activa":
        sesion.estado = "finalizada"
        sesion.fecha_fin = datetime.utcnow()
        session.add(sesion)
        await session.commit()
        await session.refresh(sesion)
    return _to_out(sesion)
