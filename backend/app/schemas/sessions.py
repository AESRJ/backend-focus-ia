from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class SessionStartIn(BaseModel):
    duration: Optional[int] = Field(None, gt=0, le=24 * 60)


class SessionOut(BaseModel):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    nivel_restriccion_sesion: Optional[Literal["bajo", "intermedio", "alto"]] = None

    model_config = {"from_attributes": True}


class SessionHistoryItem(BaseModel):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    estado: Literal["activa", "finalizada"]
    nivel_restriccion_sesion: Literal["bajo", "intermedio", "alto"]
    detecciones: int
    duracion_segundos: Optional[int] = None
