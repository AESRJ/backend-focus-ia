from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import auth_backend, fastapi_users
from .db import engine
from .models.user import User, Base  # noqa: F401
from .schemas.user import UserRead, UserRegister, UserUpdate


# --- Crear tablas al iniciar ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# --- App ---
app = FastAPI(title="Focus IA - Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro
app.include_router(
    fastapi_users.get_register_router(UserRead, UserRegister),
    prefix="/auth",
    tags=["auth"],
)

# Login JWT
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# GET /users/me y PATCH /users/me
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
