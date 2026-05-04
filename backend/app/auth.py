from typing import Any

from fastapi import Depends
from fastapi_users import FastAPIUsers, BaseUserManager, IntegerIDMixin
from fastapi_users.authentication import (
    JWTStrategy,
    AuthenticationBackend,
    BearerTransport,
)
from sqlalchemy.orm.attributes import flag_modified

from .core.config import settings
from .db import get_user_db
from .models.user import User


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.JWT_SECRET
    verification_token_secret = settings.JWT_SECRET

    async def _update(self, user: User, update_dict: dict[str, Any]) -> User:
        # `username` no es columna de la tabla — se persiste dentro del JSON
        # `profile_data` para no requerir migración.
        if "username" in update_dict:
            new_username = update_dict.pop("username")
            merged = dict(user.profile_data or {})
            if new_username is None:
                merged.pop("username", None)
            else:
                merged["username"] = new_username
            user.profile_data = merged
            flag_modified(user, "profile_data")

        return await super()._update(user, update_dict)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.JWT_SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
