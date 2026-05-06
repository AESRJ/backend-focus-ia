# Mapeo de aliases en preferencias

## Por qué

El frontend usa nombres "amigables" para los modos de restricción (`tranquilo`,
`alerta`, `absoluta`), pero el resto del backend, la BD y la extensión Chrome
usan los niveles canónicos (`bajo`, `intermedio`, `alto`).

Cuando el usuario cambiaba el modo desde la UI, la sesión se guardaba siempre
con el nivel default (`intermedio`) porque el backend recibía `"alerta"` y no lo
reconocía como un nivel válido. Resultado: las sesiones no respetaban la
preferencia.

## Solución

En `app/services/profile.py` se agregaron dos diccionarios y una función:

```python
ALIAS_TO_LEVEL = {
    "tranquilo": "bajo",
    "alerta": "intermedio",
    "absoluta": "alto",
}
LEVEL_TO_ALIAS = {v: k for k, v in ALIAS_TO_LEVEL.items()}

def normalize_level(value: str | None) -> str | None:
    """Convierte alias del frontend o valor canónico al canónico.
    Devuelve None si no se puede mapear."""
    if not value:
        return None
    v = value.strip().lower()
    if v in VALID_LEVELS:
        return v
    return ALIAS_TO_LEVEL.get(v)
```

Luego, en `app/routes/preferences.py` (POST `/preferences`):

- Se llama a `normalize_level(payload.mode)` para convertir lo que mande el
  frontend a un nivel canónico.
- Se guarda el alias original en `User.profile_data["mode_alias"]` para que el
  GET pueda devolver el mismo nombre que el frontend espera y la UI marque el
  botón correcto.
- Si hay una sesión activa, se actualiza también su snapshot
  (`Sesion.nivel_restriccion_sesion`) para que las detecciones que se registren
  desde ese momento usen el nuevo nivel.

## Endpoints

- `GET /preferences` → `{ "mode": "alerta", "duration": 35 }`
- `POST /preferences` body `{ "mode": "alerta", "duration": 35 }`

## Notas

- `duration` se guarda en `User.profile_data["duration"]` (no hay columna).
- Si el alias no existe en el mapa, se guarda solo como alias libre sin tocar
  `nivel_restriccion`. Útil para futuros modos sin migrar BD.
