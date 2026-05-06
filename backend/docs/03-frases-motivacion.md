# Frases de motivación personalizadas

## Por qué

Cuando la extensión bloquea un sitio (`blocked.html`), muestra una frase
motivacional al usuario. Antes solo había una frase fija. Se agregó la
posibilidad de que cada usuario guarde sus propias frases ("mensajes para no
rendirse en sus metas") desde el perfil.

Si el usuario no tiene frases propias, la extensión usa una lista default de 10
frases incluida en el código de la extensión.

## Storage

No se creó tabla nueva. Las frases se guardan en `User.profile_data` (columna
JSON existente):

```json
{
  "motivation_phrases": ["Frase 1", "Frase 2", ...]
}
```

## Endpoints

Definidos en `app/routes/profile.py`:

- `GET /profile/motivation-phrases` → `{ "phrases": ["..."] }`
- `PUT /profile/motivation-phrases` body `{ "phrases": ["..."] }`

## Sanitización en PUT

El endpoint limpia el input antes de guardar:

- Trim de espacios.
- Descarta strings vacíos y duplicados (case-sensitive).
- Cada frase ≤ 280 caracteres (si excede, devuelve 422).
- Máximo 20 frases (si llegan más, se trunca a las primeras 20).

```python
MAX_PHRASES = 20
MAX_PHRASE_LEN = 280

cleaned: List[str] = []
seen = set()
for raw in payload.phrases:
    text = (raw or "").strip()
    if not text or text in seen:
        continue
    if len(text) > MAX_PHRASE_LEN:
        raise HTTPException(status_code=422, detail=...)
    cleaned.append(text)
    seen.add(text)
    if len(cleaned) >= MAX_PHRASES:
        break
```

## Patrón para mutar profile_data

SQLAlchemy no detecta mutaciones in-place de columnas JSON. El patrón usado en
todos los endpoints que tocan `profile_data` es:

```python
data = dict(user.profile_data or {})  # copia
data["motivation_phrases"] = cleaned  # mutación sobre la copia
user.profile_data = data              # asignación → trigger ORM
flag_modified(user, "profile_data")   # asegurar update en BD
session.add(user)
await session.commit()
```
