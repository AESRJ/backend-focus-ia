from fastapi import FastAPI, Depends
from fastapi_users import FastAPIUsers, BaseUserManager, IntegerIDMixin
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend, BearerTransport
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator
from .models.user import User, Base
from .schemas.user import UserRead, UserRegister
from .core.config import settings

# --- Base de datos ---
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_user_db(session: Session = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)

# --- UserManager ---
class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.JWT_SECRET
    verification_token_secret = settings.JWT_SECRET

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

# --- Auth backend ---
bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.JWT_SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# --- FastAPIUsers ---
fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

# --- App ---
app = FastAPI(title="Focus IA - Backend")

app.include_router(
    fastapi_users.get_register_router(UserRead, UserRegister),
    prefix="/auth",
    tags=["auth"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)