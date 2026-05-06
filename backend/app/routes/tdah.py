"""Endpoints para guardar y consultar resultados del cuestionario TDAH.

Almacenamos el ultimo resultado en User.profile_data["tdah"] para no crear
una tabla nueva. Si en el futuro se necesita historial, se puede migrar a
una tabla dedicada.
"""
from datetime import datetime
from typing import Dict, Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ..auth import current_active_user
from ..db import get_async_session
from ..models.user import User

router = APIRouter(prefix="/tdah", tags=["tdah"])

NIVELES = {"Muy bajo", "Bajo", "Moderado", "Alto", "Muy alto"}


class TdahResultadoIn(BaseModel):
    puntaje_inatencion: int = Field(..., ge=0, le=9)
    puntaje_hiperactividad: int = Field(..., ge=0, le=9)
    puntaje_total: int = Field(..., ge=0, le=18)
    nivel_interpretacion: Literal[
        "Muy bajo", "Bajo", "Moderado", "Alto", "Muy alto"
    ]
    # Mapa de id_pregunta -> 'de_acuerdo' | 'en_desacuerdo' | null
    respuestas: Dict[str, Optional[str]] = Field(default_factory=dict)


class TdahResultadoOut(BaseModel):
    puntaje_inatencion: int
    puntaje_hiperactividad: int
    puntaje_total: int
    nivel_interpretacion: str
    completado_en: str
    respuestas: Dict[str, Optional[str]] = Field(default_factory=dict)


@router.post("/resultados", response_model=TdahResultadoOut)
async def guardar_resultado(
    payload: TdahResultadoIn,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Guarda el ultimo resultado del cuestionario TDAH del usuario."""
    completado_en = datetime.utcnow().isoformat() + "Z"
    resultado = {
        "puntaje_inatencion": payload.puntaje_inatencion,
        "puntaje_hiperactividad": payload.puntaje_hiperactividad,
        "puntaje_total": payload.puntaje_total,
        "nivel_interpretacion": payload.nivel_interpretacion,
        "completado_en": completado_en,
        "respuestas": payload.respuestas,
    }

    data = dict(user.profile_data or {})
    data["tdah"] = resultado
    user.profile_data = data
    flag_modified(user, "profile_data")
    session.add(user)
    await session.commit()

    return TdahResultadoOut(**resultado)


@router.get("/resultados", response_model=Optional[TdahResultadoOut])
async def obtener_resultado(
    user: User = Depends(current_active_user),
):
    """Devuelve el ultimo resultado guardado, o null si nunca hizo el quiz."""
    data = user.profile_data or {}
    tdah = data.get("tdah")
    if not isinstance(tdah, dict):
        return None
    try:
        return TdahResultadoOut(**tdah)
    except Exception:
        # Si por alguna razon el JSON guardado esta corrupto, devolvemos null
        # en vez de 500 para no bloquear al usuario.
        return None
