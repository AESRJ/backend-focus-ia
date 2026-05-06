# Documentación de cambios — Backend Focus IA

Notas técnicas separadas por feature. Cada archivo cubre un cambio acotado:
qué hace, por qué, cómo está implementado.

## Índice

1. [Mapeo de aliases en preferencias](./01-aliases-preferencias.md)
   Resuelve el bug de sesiones que siempre quedaban en `intermedio`.

2. [Sesión activa: nivel vivo vs snapshot](./02-sesiones-nivel-vivo.md)
   `/sessions/active` ahora refleja cambios de preferencia sin reiniciar la sesión.

3. [Frases de motivación personalizadas](./03-frases-motivacion.md)
   Endpoints para que el usuario guarde sus propias frases (las usa
   `blocked.html` de la extensión).

4. [Cuestionario TDAH](./04-tdah.md)
   `POST/GET /tdah/resultados`. Guarda el último resultado en `profile_data`.

5. [Test IQ con auto-ajuste de preferencias](./05-iq.md)
   `POST/GET /iq/resultados`. Recalcula score en backend (anti-trampa) y
   ajusta el modo + duración del usuario en la misma transacción.

## Convenciones repetidas

- **Mutar `User.profile_data` (JSON)**: copiar el dict, asignarlo de nuevo y
  llamar `flag_modified(user, "profile_data")`. SQLAlchemy no detecta
  mutaciones in-place en columnas JSON.
- **Niveles canónicos**: `bajo`, `intermedio`, `alto` (BD y extensión).
  **Aliases del frontend**: `tranquilo`, `alerta`, `absoluta`. Todo input que
  pueda venir como alias pasa por `services.profile.normalize_level()`.
- **Validación en bordes**: Pydantic con `Field(..., ge=, le=)` o `Literal[...]`
  para devolver 422 antes de tocar BD.
