from pydantic import EmailStr, Field
from fastapi_users import schemas
 
class UserRegister(schemas.BaseUserCreate):
    name: str = Field(..., min_length=2, max_length=100)
 
class UserRead(schemas.BaseUser[int]):
    name: str
 
class UserUpdate(schemas.BaseUserUpdate):
    name: str | None = None
    email: EmailStr | None = None
 