# Focus IA — Documentación de Base de Datos

**Versión:** 1.0.0  
**Motor:** MySQL 8.0+  
**ORM:** SQLAlchemy 2.0 (async)  
**Driver:** aiomysql

---

## Contenido

- [Arquitectura](#arquitectura)
- [Estructura de la base de datos](#estructura-de-la-base-de-datos)
- [Configuración del entorno](#configuración-del-entorno)
- [Despliegue en Railway](#despliegue-en-railway)
- [Cambios respecto a la versión anterior](#cambios-respecto-a-la-versión-anterior)
- [Verificación](#verificación)

---

## Arquitectura

El sistema sigue una arquitectura de tres capas donde el frontend nunca se comunica directamente con la base de datos. Toda operación sobre datos pasa por la API.

```
Frontend (Vercel)
      |
      |  HTTPS / JSON
      v
Backend API - FastAPI (Railway)
      |
      |  TCP / aiomysql (red interna Railway)
      v
Base de datos MySQL (Railway)
```

La comunicación entre el backend y MySQL usa el hostname interno `mysql.railway.internal`, disponible únicamente dentro de la red privada de Railway. Esto evita exponer la base de datos a internet.

---

## Estructura de la base de datos

### Base de datos: `railway`

### Tabla: `users`

Almacena los usuarios registrados en la plataforma. Combina los campos requeridos por `fastapi-users` con campos propios de la aplicación.

| Columna | Tipo | Nulo | Default | Descripción |
|---|---|---|---|---|
| `id` | INT | NO | AUTO_INCREMENT | Clave primaria |
| `email` | VARCHAR(255) | NO | — | Correo electrónico, único por usuario |
| `hashed_password` | VARCHAR(255) | NO | — | Contraseña cifrada con bcrypt |
| `name` | VARCHAR(100) | NO | — | Nombre del usuario |
| `profile_data` | JSON | SÍ | NULL | Datos adicionales del perfil |
| `created_at` | DATETIME | NO | CURRENT_TIMESTAMP | Fecha de registro |
| `is_active` | TINYINT(1) | NO | 1 | Indica si la cuenta está habilitada |
| `is_superuser` | TINYINT(1) | NO | 0 | Permisos de administrador |
| `is_verified` | TINYINT(1) | NO | 0 | Verificación de correo electrónico |

**Índices:**
- `PRIMARY KEY (id)`
- `UNIQUE KEY uq_users_email (email)`
- `INDEX idx_users_email (email)`

**Nota:** Los campos `is_active`, `is_superuser` e `is_verified` son requeridos por `fastapi-users`. Las tablas se crean automáticamente al iniciar la aplicación mediante `Base.metadata.create_all`.

---

## Configuración del entorno

El archivo `backend/.env` contiene las variables de conexión. Este archivo **no debe subirse al repositorio** — está incluido en `.gitignore`.

```env
DATABASE_URL=mysql+aiomysql://USUARIO:CONTRASEÑA@HOST:3306/NOMBRE_DB
JWT_SECRET=cadena-hexadecimal-de-64-caracteres-minimo
```

El formato de `DATABASE_URL` varía según el proveedor:

| Proveedor | Formato |
|---|---|
| Railway (interno) | `mysql+aiomysql://root:pass@mysql.railway.internal:3306/railway` |
| Railway (externo) | `mysql+aiomysql://root:pass@HOST_PUBLICO:PUERTO/railway` |
| Local | `mysql+aiomysql://root:pass@localhost:3306/focusia` |

Para generar un `JWT_SECRET` seguro:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

El archivo `backend/.env.example` contiene una plantilla con todos los campos requeridos sin valores reales.

---

## Despliegue en Railway

### Variables de entorno requeridas

En el panel de Railway, servicio backend → pestaña **Variables**, configurar:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | `mysql+aiomysql://root:CONTRASEÑA@mysql.railway.internal:3306/railway` |
| `JWT_SECRET` | Cadena hexadecimal segura |

> El hostname `mysql.railway.internal` solo funciona cuando ambos servicios (backend y MySQL) pertenecen al mismo proyecto en Railway. Si el backend está en un proyecto diferente, usar el hostname público con el puerto asignado.

### Inicialización de la base de datos

No es necesario ejecutar el schema manualmente. Al arrancar, el backend ejecuta:

```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

Esto crea las tablas si no existen. Si se requiere ejecutar el schema de forma manual (por ejemplo, para migraciones o auditoría), el archivo `database/schema.sql` contiene las instrucciones completas:

```bash
mysql -h HOST -u USUARIO -p NOMBRE_DB < database/schema.sql
```

### Root directory en Railway

Al conectar el repositorio GitHub al servicio backend en Railway, configurar el **Root Directory** como `backend`. Railway detectará el `Dockerfile` en esa ruta y lo usará para construir el contenedor.

---

## Cambios respecto a la versión anterior

La versión anterior usaba **Microsoft SQL Server (Azure)** con drivers ODBC. A continuación se detalla qué cambió y por qué.

### `backend/requirements.txt`

| Paquete eliminado | Reemplazado por | Motivo |
|---|---|---|
| `aioodbc` | `aiomysql==0.2.0` | Driver async para MySQL |
| `pyodbc` | `PyMySQL==1.1.1` | Cliente MySQL puro Python |

### `backend/app/main.py`

Se eliminó la transformación de URL que adaptaba el esquema de conexión de SQL Server, y se agregó el evento `lifespan` para creación automática de tablas:

```python
# Antes — transformación específica de SQL Server
DATABASE_URL = settings.DATABASE_URL.replace("mssql+pyodbc://", "mssql+aioodbc://")

# Ahora — URL directa, sin transformación
DATABASE_URL = settings.DATABASE_URL
```

```python
# Agregado — crea las tablas al iniciar si no existen
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
```

### `backend/Dockerfile`

Se sustituyeron las dependencias de Microsoft ODBC Driver (~500 MB) por las librerías de cliente MySQL:

```dockerfile
# Antes
RUN apt-get install -y unixodbc unixodbc-dev curl gnupg2 apt-transport-https
# + instalación de msodbcsql18 desde repositorio de Microsoft

# Ahora
RUN apt-get install -y default-libmysqlclient-dev gcc
```

---

## Verificación

Una vez desplegado, confirmar que el servicio está activo con los siguientes endpoints:

**Registrar usuario:**
```bash
curl -X POST https://TU_DOMINIO/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "usuario@ejemplo.com", "password": "contraseña123", "name": "Nombre"}'
```

**Iniciar sesión:**
```bash
curl -X POST https://TU_DOMINIO/auth/jwt/login \
  -d "username=usuario@ejemplo.com&password=contraseña123"
```

**Consultar usuario autenticado:**
```bash
curl https://TU_DOMINIO/users/me \
  -H "Authorization: Bearer TOKEN"
```

Para confirmar que la tabla `users` fue creada correctamente en Railway, usar la consola de variables o conectarse con un cliente MySQL:

```sql
SHOW TABLES;
DESCRIBE users;
```
