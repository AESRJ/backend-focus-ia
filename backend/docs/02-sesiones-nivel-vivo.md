# Sesión activa: nivel "vivo" vs snapshot

## Por qué

`GET /sessions/active` antes devolvía siempre el snapshot guardado en
`Sesion.nivel_restriccion_sesion` (el nivel con el que arrancó la sesión).
Si el usuario cambiaba la preferencia a la mitad de una sesión, la extensión
seguía usando el nivel viejo hasta reiniciar la sesión.

## Solución

En `app/routes/sessions.py`, el endpoint `/sessions/active` ahora lee el nivel
**actual** del perfil y lo devuelve como nivel efectivo:

```python
@router.get("/active", response_model=Optional[SessionOut])
async def get_active_session(...):
    sesion = ...  # busca la sesión activa
    if sesion is None:
        return None

    perfil = await get_or_create_profile(session, user.id)
    nivel_vivo = perfil.nivel_restriccion or sesion.nivel_restriccion_sesion or "intermedio"
    return SessionOut(
        id=sesion.id,
        start_time=sesion.fecha_inicio,
        end_time=sesion.fecha_fin,
        nivel_restriccion_sesion=nivel_vivo,
    )
```

## Importante

El snapshot en `Sesion.nivel_restriccion_sesion` **no se borra** ni se sobrescribe
al consultar. Solo se sincroniza cuando el usuario explícitamente cambia la
preferencia (en POST `/preferences`). Esto se hace para:

- Que los registros de detección (`RegistroDeteccion.nivel_restriccion_activo`)
  queden con el nivel real en el momento de la detección.
- Que el histórico siga reflejando con qué nivel se completó cada sesión.

## Flujo end-to-end

1. Usuario inicia sesión con `tranquilo` (canonical: `bajo`).
2. Mid-sesión cambia a `absoluta`. El POST `/preferences` actualiza
   `PerfilEstudiante.nivel_restriccion = "alto"` y sincroniza el snapshot.
3. La extensión hace polling a `/sessions/active` y recibe `"alto"`.
4. Las detecciones siguientes se registran con `nivel_restriccion_activo = "alto"`.
