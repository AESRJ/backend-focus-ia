from pydantic import BaseModel, Field


class PreferenceIn(BaseModel):
    mode: str = Field(..., min_length=1, max_length=50)
    duration: int = Field(..., gt=0, le=24 * 60)


class PreferenceOut(BaseModel):
    mode: str
    duration: int
