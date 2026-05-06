"""Endpoints para guardar y consultar resultados del test IQ.

Almacenamos el ultimo resultado en User.profile_data["iq"]. Ademas, segun el
porcentaje de aciertos, ajustamos automaticamente las preferencias del
estudiante (nivel_restriccion + duration) en la misma transaccion:

  < 40 %  aciertos -> nivel "alto"        (alias 'absoluta', 25 min)
  40-70 % aciertos -> nivel "intermedio"  (alias 'alerta',   35 min)
  > 70 %  aciertos -> nivel "bajo"        (alias 'tranquilo', 50 min)

Logica: puntaje bajo => necesita mas restriccion para concentrarse.
Puntaje alto => ya autorregula bien, modo mas permisivo.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ..auth import current_active_user
from ..db import get_async_session
from ..models.sesion import Sesion
from ..models.user import User
from ..services.profile import LEVEL_TO_ALIAS, get_or_create_profile

router = APIRouter(prefix="/iq", tags=["iq"])


# Indice correcto de cada pregunta (espejo del IQ_QUESTIONS del frontend).
# Tener esto en backend evita confiar ciegamente en el isCorrect del cliente
# y permite recalcular el score de forma autoritativa.
CORRECT_INDEX = {
    1: 2, 2: 2, 3: 1, 4: 2, 5: 0, 6: 2, 7: 2, 8: 1, 9: 3, 10: 0,
    11: 1, 12: 1, 13: 2, 14: 2, 15: 1, 16: 2, 17: 2, 18: 2, 19: 2, 20: 2,
    21: 1, 22: 2, 23: 1, 24: 2, 25: 3, 26: 2, 27: 2, 28: 0, 29: 1, 30: 1,
}

TOTAL_QUESTIONS = len(CORRECT_INDEX)


class IqAnswerIn(BaseModel):
    questionId: int = Field(..., ge=1, le=TOTAL_QUESTIONS)
    selectedIndex: int = Field(..., ge=0, le=3)
    isCorrect: Optional[bool] = None  # ignorado: se recalcula en backend
    timeSpentMs: int = Field(..., ge=0)


class IqResultadoIn(BaseModel):
    answers: List[IqAnswerIn]
    totalTimeMs: int = Field(..., ge=0)
    completedAt: Optional[str] = None  # se sobreescribe con la hora del server


class IqResultadoOut(BaseModel):
    score: int
    total_questions: int
    percentage: float
    nivel_interpretacion: str
    mode_recomendado: str
    duracion_recomendada: int
    total_time_ms: int
    completado_en: str


def _interpretar(score: int) -> dict:
    """Mapea aciertos -> (nivel canonico, alias, duration) segun la tabla."""
    pct = (score / TOTAL_QUESTIONS) * 100 if TOTAL_QUESTIONS else 0
    if pct < 40:
        nivel_canonico = "alto"
        nivel_label = "Bajo"
        duration = 25
    elif pct <= 70:
        nivel_canonico = "intermedio"
        nivel_label = "Promedio"
        duration = 35
    else:
        nivel_canonico = "bajo"
        nivel_label = "Alto"
        duration = 50
    return {
        "percentage": round(pct, 2),
        "nivel_canonico": nivel_canonico,
        "nivel_label": nivel_label,
        "alias": LEVEL_TO_ALIAS[nivel_canonico],
        "duration": duration,
    }


@router.post("/resultados", response_model=IqResultadoOut)
async def guardar_resultado(
    payload: IqResultadoIn,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Guarda el resultado del IQ y ajusta automaticamente las preferencias."""
    # 1) Recalcular score autoritativo en backend
    score = 0
    answers_clean = []
    for a in payload.answers:
        is_correct = CORRECT_INDEX.get(a.questionId) == a.selectedIndex
        if is_correct:
            score += 1
        answers_clean.append({
            "question_id": a.questionId,
            "selected_index": a.selectedIndex,
            "is_correct": is_correct,
            "time_spent_ms": a.timeSpentMs,
        })

    interp = _interpretar(score)
    completado_en = datetime.utcnow().isoformat() + "Z"

    resultado = {
        "score": score,
        "total_questions": TOTAL_QUESTIONS,
        "percentage": interp["percentage"],
        "nivel_interpretacion": interp["nivel_label"],
        "mode_recomendado": interp["alias"],
        "duracion_recomendada": interp["duration"],
        "total_time_ms": payload.totalTimeMs,
        "completado_en": completado_en,
        "answers": answers_clean,
    }

    # 2) Guardar resultado en profile_data["iq"]
    data = dict(user.profile_data or {})
    data["iq"] = resultado
    # 3) Ajustar preferencias automaticamente
    data["mode_alias"] = interp["alias"]
    data["duration"] = interp["duration"]
    user.profile_data = data
    flag_modified(user, "profile_data")
    session.add(user)

    # 4) Actualizar PerfilEstudiante.nivel_restriccion (fuente de verdad)
    perfil = await get_or_create_profile(session, user.id)
    perfil.nivel_restriccion = interp["nivel_canonico"]
    perfil.updated_at = datetime.utcnow()
    session.add(perfil)

    # 5) Si hay sesion activa, sincronizar su snapshot
    activa = (
        await session.execute(
            select(Sesion).where(
                Sesion.estudiante_id == user.id,
                Sesion.estado == "activa",
            )
        )
    ).scalars().first()
    if activa is not None:
        activa.nivel_restriccion_sesion = interp["nivel_canonico"]
        session.add(activa)

    await session.commit()

    return IqResultadoOut(
        score=score,
        total_questions=TOTAL_QUESTIONS,
        percentage=interp["percentage"],
        nivel_interpretacion=interp["nivel_label"],
        mode_recomendado=interp["alias"],
        duracion_recomendada=interp["duration"],
        total_time_ms=payload.totalTimeMs,
        completado_en=completado_en,
    )


@router.get("/resultados", response_model=Optional[IqResultadoOut])
async def obtener_resultado(
    user: User = Depends(current_active_user),
):
    """Devuelve el ultimo resultado guardado, o null si nunca hizo el test."""
    data = user.profile_data or {}
    iq = data.get("iq")
    if not isinstance(iq, dict):
        return None
    try:
        return IqResultadoOut(
            score=iq["score"],
            total_questions=iq["total_questions"],
            percentage=iq["percentage"],
            nivel_interpretacion=iq["nivel_interpretacion"],
            mode_recomendado=iq["mode_recomendado"],
            duracion_recomendada=iq["duracion_recomendada"],
            total_time_ms=iq.get("total_time_ms", 0),
            completado_en=iq["completado_en"],
        )
    except (KeyError, TypeError):
        return None
