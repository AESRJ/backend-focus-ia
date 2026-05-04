from pydantic import EmailStr, Field
from fastapi_users import schemas
 
class UserRegister(schemas.BaseUserCreate):
    name: str = Field(..., min_length=2, max_length=100)
 
class UserRead(schemas.BaseUser[int]):
    name: str
    username: str | None = None

class UserUpdate(schemas.BaseUserUpdate):
    name: str | None = None
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=50, pattern=r"^[a-zA-ZñÑ0-9_]+$")
 