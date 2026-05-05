from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_active_user
from ..db import get_async_session
from ..models.distractor import Distractor
from ..models.registro_deteccion import RegistroDeteccion
from ..models.sesion import Sesion
from ..models.user import User
from ..schemas.detections import DetectionCreate, DetectionOut

router = APIRouter(prefix="/sessions", tags=["detections"])


def _format_ts(dt: datetime) -> str:
    """Formato YYYY-MM-DD|HH:MM:SS según el modelo."""
    return dt.strftime("%Y-%m-%d|%H:%M:%S")


async def _get_owned_session(
    session: AsyncSession, user_id: int, session_id: int
) -> Sesion:
    sesion = await session.get(Sesion, session_id)
    if sesion is None or sesion.estudiante_id != user_id:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return sesion


async def _resolve_distractor(
    session: AsyncSession,
    user_id: int,
    distractor_id: int | None,
    identificador: str | None,
) -> Distractor:
    """Resuelve el distractor por id o por identificador. Solo permite
    globales o personales del usuario."""
    if distractor_id is not None:
        d = await session.get(Distractor, distractor_id)
        if d is None or (d.origen == "personal" and d.estudiante_id != user_id):
            raise HTTPException(status_code=404, detail="Distractor no encontrado")
        return d

    if not identificador:
        raise HTTPException(
            status_code=422,
            detail="Debe enviar 'distractor_id' o 'identificador'",
        )

    result = await session.execute(
        select(Distractor).where(
            Distractor.identificador == identificador,
            or_(
                Distractor.origen == "global",
                (Distractor.origen == "personal")
                & (Distractor.estudiante_id == user_id),
            ),
        )
    )
    d = result.scalars().first()
    if d is None:
        raise HTTPException(
            status_code=404,
            detail=f"Distractor con identificador '{identificador}' no encontrado",
        )
    return d


@router.post(
    "/{session_id}/detections",
    response_model=DetectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_detection(
    session_id: int,
    payload: DetectionCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Registra un evento de detección durante una sesión activa."""
    sesion = await _get_owned_session(session, user.id, session_id)
    if sesion.estado != "activa":
        raise HTTPException(
            status_code=409,
            detail="No se pueden registrar detecciones en una sesión finalizada",
        )

    distractor = await _resolve_distractor(
        session, user.id, payload.distractor_id, payload.identificador
    )

    timestamp_str = payload.timestamp_deteccion or _format_ts(datetime.utcnow())

    registro = RegistroDeteccion(
        sesion_id=sesion.id,
        distractor_id=distractor.id,
        nombre_detectado=payload.nombre_detectado,
        categoria=payload.categoria,
        # Snapshot del nivel activo en el momento de la detección.
        # Fallback a 'intermedio' para cubrir sesiones legacy con nivel NULL.
        nivel_restriccion_activo=sesion.nivel_restriccion_sesion or "intermedio",
        timestamp_deteccion=timestamp_str,
    )
    session.add(registro)
    await session.commit()
    await session.refresh(registro)
    return registro


@router.get(
    "/{session_id}/detections",
    response_model=List[DetectionOut],
)
async def list_detections(
    session_id: int,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Lista todas las detecciones de una sesión propia, ordenadas por
    timestamp ascendente."""
    await _get_owned_session(session, user.id, session_id)

    result = await session.execute(
        select(RegistroDeteccion)
        .where(RegistroDeteccion.sesion_id == session_id)
        .order_by(RegistroDeteccion.timestamp_nativo.asc())
    )
    return result.scalars().all()
