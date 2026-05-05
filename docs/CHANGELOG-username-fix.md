# Fix — `username` no se guardaba al actualizar perfil

## Problema

`PATCH /users/me` respondía `200 OK` pero el `username` nunca se persistía en BD. El frontend enviaba el campo, el backend lo descartaba en silencio (no existía en `UserUpdate` ni como columna en `users`).

## Solución

Se persiste `username` dentro del JSON `profile_data` del modelo `User`. **Sin migración de BD**.

## Archivos modificados

- `backend/app/models/user.py` — `@property username` que lee de `profile_data["username"]`.
- `backend/app/schemas/user.py` — `UserRead` y `UserUpdate` ahora exponen/aceptan `username` (validado con regex `^[a-zA-ZñÑ0-9_]+$`, 3–50 chars).
- `backend/app/auth.py` — override de `UserManager._update` que enruta `username` a `profile_data` con `flag_modified`.

## Cómo probar tras deploy a Railway

1. `GET /users/me` → la respuesta incluye `username` (`null` para usuarios viejos).
2. `PATCH /users/me` con `{"username": "nuevo_user"}` → debe devolver el `username` actualizado.
3. Recargar el perfil en el frontend → el valor persiste.

## Notas

- No requiere `alembic upgrade`: solo redeploy.
- **Pendiente futuro:** no hay constraint de unicidad en `username` mientras viva en JSON. Si se necesita, migrar a columna real con índice único.
