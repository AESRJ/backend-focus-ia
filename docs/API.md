# Focus IA — Referencia de la API

Documento de referencia para los endpoints disponibles en el backend.
Pensado para que el equipo de frontend (y quien revise el repositorio)
sepa qué expone cada módulo, qué espera recibir y qué devuelve.

> Para el detalle interactivo conviene también abrir `https://TU_DOMINIO/docs`
> (Swagger UI generado automáticamente por FastAPI).

## Contenido

- [Convenciones](#convenciones)
- [Autenticación](#autenticación)
- [Usuarios](#usuarios)
- [Perfil de restricción](#perfil-de-restricción)
- [Preferencias](#preferencias)
- [Sesiones de focus](#sesiones-de-focus)
- [Distractores](#distractores)
- [Detecciones](#detecciones)
- [Modelo de datos](#modelo-de-datos)

---

## Convenciones

- Todas las rutas (excepto `/auth/register` y `/auth/jwt/login`) requieren
  el header `Authorization: Bearer <token>`.
- Los timestamps en respuestas se devuelven en ISO 8601 (`datetime`),
  salvo `timestamp_deteccion` que usa el formato textual
  `YYYY-MM-DD|HH:MM:SS` por requerimiento del frontend.
- Los enums están definidos como `Literal` en Pydantic. Cualquier valor
  fuera del conjunto válido devuelve `422`.
- Los errores siguen el formato estándar de FastAPI:
  `{ "detail": "mensaje" }`.

### Niveles de restricción

| Nivel | Comportamiento esperado en cliente |
|---|---|
| `bajo` | Registra la detección en silencio, sin alertar al usuario |
| `intermedio` | Muestra un toast/aviso visual |
| `alto` | Bloquea o redirige fuera del distractor |

---

## Autenticación

Provistos por `fastapi-users`.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/register` | Crea un usuario nuevo |
| POST | `/auth/jwt/login` | Devuelve un bearer token |
| POST | `/auth/jwt/logout` | Invalida la sesión actual |

**Registro** — payload:

```json
{
  "email": "alumno@ejemplo.com",
  "password": "claveSegura123",
  "name": "Nombre Apellido"
}
```

**Login** — `application/x-www-form-urlencoded`:

```
username=alumno@ejemplo.com&password=claveSegura123
```

Respuesta:

```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

## Usuarios

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/users/me` | Devuelve el usuario autenticado |
| PATCH | `/users/me` | Actualiza nombre, email o `profile_data` |

---

## Perfil de restricción

Maneja el nivel global del estudiante. El nivel se aplica al iniciar una
sesión nueva; las sesiones en curso conservan el snapshot con el que
arrancaron.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/profile/restriction` | Devuelve `{ nivel_restriccion, updated_at }` |
| PATCH | `/profile/restriction` | Actualiza el nivel. Body: `{ "nivel_restriccion": "alto" }` |

Si el perfil aún no existe, el primer GET lo crea con nivel
`intermedio`.

---

## Preferencias

Combina dos fuentes:

- `mode` → se persiste en `perfiles_estudiante.nivel_restriccion`
  cuando coincide con un nivel válido.
- `duration` (minutos) → se guarda en `users.profile_data` como JSON.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/preferences` | Devuelve `{ mode, duration }` |
| POST | `/preferences` | Guarda ambos valores en una sola llamada |

Si `mode` es un valor libre fuera del enum (por ejemplo `"tranquilo"`),
se conserva en `profile_data.mode_alias` sin tocar el nivel oficial. El
`duration` admite cualquier valor `1 ≤ n ≤ 1440`.

---

## Sesiones de focus

Una sesión representa un bloque de trabajo. Sólo puede haber **una
sesión activa por usuario**; un POST que llega cuando ya existe una
activa devuelve la existente en lugar de crear una nueva.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/sessions` | Inicia una sesión (o reutiliza la activa) |
| GET | `/sessions/active` | Devuelve la activa o `null` |
| GET | `/sessions/history` | Histórico paginado, más recientes primero |
| PATCH | `/sessions/{id}` | Marca la sesión como `finalizada` |

`GET /sessions/history` admite `?limit=` (1-200, default 50) y
`?offset=`. Cada elemento incluye duración en segundos y conteo de
detecciones, calculados con un único query (subselect + outer join) para
evitar N+1.

---

## Distractores

Catálogo combinado: la tabla mezcla entradas globales (sembradas por el
equipo) y personales (creadas por cada usuario). Los globales son sólo
lectura — los intentos de PATCH/DELETE devuelven `403`.

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/distractors?origen=all\|global\|personal` | Lista visible para el usuario |
| POST | `/distractors` | Crea un distractor personal |
| GET | `/distractors/{id}` | Devuelve uno (sólo si es global o propio) |
| PATCH | `/distractors/{id}` | Edita uno propio |
| DELETE | `/distractors/{id}` | Borra uno propio |

Body de creación:

```json
{
  "nombre": "TikTok",
  "identificador": "tiktok.com",
  "tipo": "url",
  "categoria": "red_social"
}
```

`identificador` representa el hostname (cuando `tipo = url`) o el nombre
del proceso (cuando `tipo = proceso`, pensado para una eventual
extensión de escritorio).

---

## Detecciones

Eventos registrados durante una sesión activa. La sesión debe existir,
pertenecer al usuario autenticado y estar en estado `activa` —
si está finalizada se devuelve `409`.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/sessions/{id}/detections` | Registra un evento |
| GET | `/sessions/{id}/detections` | Lista los eventos de la sesión |

Body de creación (cualquiera de las dos formas de identificar el
distractor es válida):

```json
{
  "distractor_id": 12,
  "nombre_detectado": "Reddit",
  "categoria": "red_social",
  "timestamp_deteccion": "2026-04-28|14:35:22"
}
```

```json
{
  "identificador": "reddit.com",
  "nombre_detectado": "Reddit",
  "categoria": "red_social"
}
```

Si se omite `timestamp_deteccion`, el servidor genera el valor en el
momento de recibir la petición. El campo `nivel_restriccion_activo` se
copia desde la sesión en ese momento, no desde el perfil — así se
preserva la lógica con la que el cliente actuó aunque el usuario haya
cambiado su configuración después.

---

## Modelo de datos

Resumen de las tablas creadas por `Base.metadata.create_all` al
arrancar el backend.

### `users`

Ya documentada en `docs/DATABASE.md`. La integración con `fastapi-users`
maneja el hashing de la contraseña y los flags de control.

### `perfiles_estudiante`

Relación 1:1 con `users`. Guarda el nivel de restricción global. Default
`'intermedio'`.

| Columna | Tipo | Notas |
|---|---|---|
| `id` | INT PK | |
| `estudiante_id` | INT FK→users.id, UNIQUE | |
| `nivel_restriccion` | ENUM('bajo','intermedio','alto') | default `intermedio` |
| `updated_at` | DATETIME | onupdate |

### `sesiones`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | INT PK | |
| `estudiante_id` | INT FK→users.id | |
| `nivel_restriccion_sesion` | ENUM(...) | snapshot al iniciar |
| `fecha_inicio` | DATETIME | default now |
| `fecha_fin` | DATETIME NULL | se completa al finalizar |
| `estado` | ENUM('activa','finalizada') | default `activa` |

Índice compuesto `(estudiante_id, estado)` para encontrar la sesión
activa de un estudiante en O(log n).

### `distractores`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | INT PK | |
| `nombre` | VARCHAR(100) | |
| `identificador` | VARCHAR(255) | hostname o nombre de proceso |
| `tipo` | ENUM('url','proceso') | |
| `categoria` | ENUM('red_social','videojuego','streaming','otro') | |
| `origen` | ENUM('global','personal') | |
| `estudiante_id` | INT FK→users.id NULL | obligatorio si origen='personal' |
| `created_at` / `updated_at` | DATETIME | |

Índices: `(identificador)` para matching en tiempo real,
`(origen, estudiante_id)` para listados.

### `registros_deteccion`

| Columna | Tipo | Notas |
|---|---|---|
| `id` | INT PK | |
| `sesion_id` | INT FK→sesiones.id | |
| `distractor_id` | INT FK→distractores.id | |
| `nombre_detectado` | VARCHAR(100) | snapshot |
| `categoria` | ENUM(...) | snapshot |
| `nivel_restriccion_activo` | ENUM(...) | snapshot del nivel al detectar |
| `timestamp_deteccion` | VARCHAR(20) | formato `YYYY-MM-DD|HH:MM:SS` |
| `timestamp_nativo` | DATETIME | default now, usado para ordenar |

Los snapshots de `nombre_detectado`, `categoria` y
`nivel_restriccion_activo` son intencionales: si después se modifica el
distractor o el nivel del perfil, el histórico sigue siendo fiel a lo
que ocurrió en su momento.
