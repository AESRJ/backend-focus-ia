from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RestrictionLevel = Literal["bajo", "intermedio", "alto"]


class RestrictionProfileOut(BaseModel):
    nivel_restriccion: RestrictionLevel
    updated_at: datetime

    model_config = {"from_attributes": True}


class RestrictionProfileUpdate(BaseModel):
    nivel_restriccion: RestrictionLevel
