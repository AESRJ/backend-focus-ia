from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import auth_backend, fastapi_users
from .db import engine
from .models.user import User, Base  # noqa: F401
from .models.distractor import Distractor  # noqa: F401 — registra tabla en Base.metadata
from .models.perfil_estudiante import PerfilEstudiante  # noqa: F401
from .models.sesion import Sesion  # noqa: F401
from .models.registro_deteccion import RegistroDeteccion  # noqa: F401
from .schemas.user import UserRead, UserRegister, UserUpdate
from .routes.detections import router as detections_router
from .routes.distractors import router as distractors_router
from .routes.preferences import router as preferences_router
from .routes.profile import router as profile_router
from .routes.sessions import router as sessions_router
from .routes.tdah import router as tdah_router
from .routes.iq import router as iq_router


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

# Preferencias del estudiante (mode, duration)
app.include_router(preferences_router)

# Sesiones de focus
app.include_router(sessions_router)

# CRUD de distractores (globales + personales)
app.include_router(distractors_router)

# Eventos de detección por sesión (POST/GET /sessions/{id}/detections)
app.include_router(detections_router)

# Perfil de restricción del estudiante (GET/PATCH /profile/restriction)
app.include_router(profile_router)

# Resultados del cuestionario TDAH (POST/GET /tdah/resultados)
app.include_router(tdah_router)

# Resultados del test IQ (POST/GET /iq/resultados) — ajusta preferencias auto
app.include_router(iq_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
