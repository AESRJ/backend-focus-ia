# Historia: Identificador de páginas y aplicaciones no deseadas

## Descripción

**Como:** Estudiante
**Quiero:** El sistema detecte cuando accedo a páginas o aplicaciones no deseadas durante una sesión activa
**Para:** Recibir una respuesta acorde al nivel de restricción que configuré en mi perfil y mantener mi concentración.

---

## Requerimientos de Base de Datos

Esta historia requiere la definición de las siguientes entidades y sus relaciones en la base de datos.

### 1. Tabla: `distractores`

Almacena las páginas web y aplicaciones catalogadas como distractoras.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER / UUID | PK, NOT NULL, AUTO_INCREMENT | Identificador único del distractor |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre descriptivo (ej. "Facebook", "Steam") |
| `identificador` | VARCHAR(255) | NOT NULL | URL (ej. `facebook.com`) o nombre del proceso (ej. `steam.exe`) |
| `tipo` | ENUM('url', 'proceso') | NOT NULL | Indica si el identificador es URL o proceso |
| `categoria` | ENUM('red_social', 'videojuego', 'streaming', 'otro') | NOT NULL | Categoría del distractor |
| `origen` | ENUM('global', 'personal') | NOT NULL | Si es del catálogo global o personal del estudiante |
| `estudiante_id` | INTEGER / UUID | FK → estudiantes(id), NULL | Solo se llena si `origen = 'personal'` |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Fecha de creación |
| `updated_at` | TIMESTAMP | NOT NULL | Fecha de última modificación |

**Consideraciones:**
- Si `origen = 'global'`, `estudiante_id` debe ser NULL.
- Si `origen = 'personal'`, `estudiante_id` es obligatorio.
- Índice en `identificador` para búsquedas rápidas durante el monitoreo en tiempo real.
- Índice compuesto en (`origen`, `estudiante_id`) para filtrar distractores por estudiante.

---

### 2. Tabla: `perfiles_estudiante` (o campo en tabla `estudiantes`)

Almacena la configuración del nivel de restricción del estudiante.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER / UUID | PK, NOT NULL | Identificador del perfil |
| `estudiante_id` | INTEGER / UUID | FK → estudiantes(id), NOT NULL, UNIQUE | Referencia al estudiante |
| `nivel_restriccion` | ENUM('bajo', 'intermedio', 'alto') | NOT NULL, DEFAULT 'intermedio' | Nivel de restricción configurado |
| `updated_at` | TIMESTAMP | NOT NULL | Fecha de última modificación del nivel |

**Consideraciones:**
- El valor por defecto al crear una cuenta debe ser `'intermedio'`.
- Los cambios en este nivel **no afectan la sesión en curso**; se aplican en la siguiente sesión.

---

### 3. Tabla: `sesiones`

Representa las sesiones activas de estudio del estudiante. Es requerida porque la detección aplica únicamente durante sesiones activas.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER / UUID | PK, NOT NULL | Identificador de la sesión |
| `estudiante_id` | INTEGER / UUID | FK → estudiantes(id), NOT NULL | Estudiante dueño de la sesión |
| `nivel_restriccion_sesion` | ENUM('bajo', 'intermedio', 'alto') | NOT NULL | Nivel aplicado al iniciar la sesión (snapshot) |
| `fecha_inicio` | TIMESTAMP | NOT NULL | Inicio de la sesión |
| `fecha_fin` | TIMESTAMP | NULL | Fin de la sesión (NULL si está activa) |
| `estado` | ENUM('activa', 'finalizada') | NOT NULL, DEFAULT 'activa' | Estado actual de la sesión |

**Consideraciones:**
- El campo `nivel_restriccion_sesion` es un **snapshot** del nivel en el momento del inicio. Así se garantiza que los cambios en el perfil no afecten la sesión en curso.
- Índice en (`estudiante_id`, `estado`) para localizar rápidamente la sesión activa.

---

### 4. Tabla: `registros_deteccion`

Almacena cada detección de acceso a un distractor durante una sesión activa.

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | INTEGER / UUID | PK, NOT NULL | Identificador del registro |
| `sesion_id` | INTEGER / UUID | FK → sesiones(id), NOT NULL | Sesión en la que ocurrió la detección |
| `distractor_id` | INTEGER / UUID | FK → distractores(id), NOT NULL | Distractor detectado |
| `nombre_detectado` | VARCHAR(100) | NOT NULL | Nombre de la página/app detectada |
| `categoria` | ENUM('red_social', 'videojuego', 'streaming', 'otro') | NOT NULL | Categoría al momento de la detección |
| `nivel_restriccion_activo` | ENUM('bajo', 'intermedio', 'alto') | NOT NULL | Nivel vigente al momento de la detección |
| `timestamp_deteccion` | VARCHAR(20) | NOT NULL | Formato exacto: `2026-04-12\|14:35:22` |

**Consideraciones:**
- El formato del timestamp es un string literal con el formato `YYYY-MM-DD|HH:MM:SS` (usando el carácter `|` como separador).
- Se recomienda guardar también un `TIMESTAMP` nativo en paralelo para facilitar consultas y ordenamientos, aunque la historia exige el formato textual.
- Índice en `sesion_id` para consultas de historial por sesión.
- Índice en `timestamp_deteccion` para consultas cronológicas.

---

## Relaciones entre tablas

```
estudiantes (1) ───── (1) perfiles_estudiante
     │
     │ (1)
     ├──────── (N) sesiones
     │              │
     │              │ (1)
     │              └────── (N) registros_deteccion
     │                             │
     │                             │ (N)
     │ (1)                         │
     └──────── (N) distractores ───┘
                   [origen = personal]
```

---

## Datos iniciales (seed) sugeridos

### Distractores globales (`origen = 'global'`)

Se recomienda precargar distractores comunes para que todos los estudiantes los tengan disponibles desde el inicio:

- **Redes sociales:** Facebook, Instagram, X (Twitter), TikTok, Reddit
- **Streaming:** YouTube, Netflix, Twitch, Disney+, Spotify
- **Videojuegos:** Steam, Epic Games, Roblox, League of Legends
- **Otros:** según criterio del equipo

### Valores por defecto

- `perfiles_estudiante.nivel_restriccion` → `'intermedio'` al crear cuenta.
- `sesiones.estado` → `'activa'` al crear una sesión.

---

## Reglas de negocio relevantes para la base de datos

1. Un estudiante solo puede tener **una sesión activa** (`estado = 'activa'`) a la vez. Se recomienda validar con un constraint único parcial o a nivel de aplicación.
2. Los cambios en `perfiles_estudiante.nivel_restriccion` **no modifican** el campo `sesiones.nivel_restriccion_sesion` de la sesión activa.
3. Las consultas de monitoreo deben combinar distractores globales + personales del estudiante:
   ```sql
   SELECT * FROM distractores
   WHERE origen = 'global'
      OR (origen = 'personal' AND estudiante_id = :estudiante_id);
   ```
4. Los registros de detección deben persistir **independientemente** del nivel de restricción (incluso en nivel `bajo` se registra el evento).
