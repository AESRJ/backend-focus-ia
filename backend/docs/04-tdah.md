# Cuestionario TDAH

## Qué es

Endpoint para guardar el resultado del cuestionario TDAH (18 preguntas
divididas en inatención e hiperactividad). Se guarda solo el último resultado
por usuario.

## Storage

En `User.profile_data["tdah"]`. No se creó tabla porque por ahora solo nos
interesa el último resultado, no historial.

```json
{
  "tdah": {
    "puntaje_inatencion": 5,
    "puntaje_hiperactividad": 4,
    "puntaje_total": 9,
    "nivel_interpretacion": "Moderado",
    "completado_en": "2026-05-06T14:30:00Z",
    "respuestas": { "1": "de_acuerdo", "2": "en_desacuerdo", ... }
  }
}
```

## Endpoints

Definidos en `app/routes/tdah.py`:

- `POST /tdah/resultados` body con `puntaje_inatencion`, `puntaje_hiperactividad`,
  `puntaje_total`, `nivel_interpretacion`, `respuestas`.
- `GET /tdah/resultados` → último resultado o `null`.

## Validación con Pydantic

```python
class TdahResultadoIn(BaseModel):
    puntaje_inatencion: int = Field(..., ge=0, le=9)
    puntaje_hiperactividad: int = Field(..., ge=0, le=9)
    puntaje_total: int = Field(..., ge=0, le=18)
    nivel_interpretacion: Literal[
        "Muy bajo", "Bajo", "Moderado", "Alto", "Muy alto"
    ]
    respuestas: Dict[str, Optional[str]] = Field(default_factory=dict)
```

Pydantic rechaza con 422 si los puntajes están fuera de rango o el nivel no
es uno de los 5 valores permitidos.

## Robustez del GET

Si el JSON guardado quedó corrupto por alguna razón (un dato viejo, migración,
etc.), el endpoint devuelve `null` en lugar de 500 para no bloquear al usuario:

```python
try:
    return TdahResultadoOut(**tdah)
except Exception:
    return None
```

## Posible extensión futura

Si se necesita historial de resultados, migrar a una tabla
`resultados_tdah(user_id, completado_en, ...)` con la lógica de "tomar el más
reciente" en consultas. Por ahora YAGNI.
