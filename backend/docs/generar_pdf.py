"""
Genera PDF guía para exponer el backend de Focus IA.
Uso: python generar_pdf.py
"""
from fpdf import FPDF
from pathlib import Path

OUT = Path(__file__).parent / "presentacion-backend.pdf"

PRIMARY = (30, 64, 175)      # azul
ACCENT = (16, 185, 129)      # verde
DARK = (30, 41, 59)
GRAY = (100, 116, 139)
LIGHT = (241, 245, 249)


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*GRAY)
        self.cell(0, 8, "Focus IA - Guia de exposicion del backend", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 8, f"Pagina {self.page_no()}", align="C")

    def h1(self, text):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*PRIMARY)
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*PRIMARY)
        self.set_line_width(0.6)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def h2(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*DARK)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def h3(self, text):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*ACCENT)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")

    def body(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5.5, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5.5, "  - " + text, new_x="LMARGIN", new_y="NEXT")

    def code(self, text):
        self.set_fill_color(*LIGHT)
        self.set_font("Courier", "", 9)
        self.set_text_color(*DARK)
        self.multi_cell(0, 4.8, text, fill=True, border=0,
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def quote(self, label, text):
        self.set_fill_color(*LIGHT)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*PRIMARY)
        self.multi_cell(0, 5.5, label, fill=True,
                        new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        self.set_fill_color(*LIGHT)
        self.multi_cell(0, 5.5, text, fill=True,
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(2)


pdf = PDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(left=18, top=15, right=18)

# ============== PORTADA ==============
pdf.add_page()
pdf.ln(40)
pdf.set_font("Helvetica", "B", 28)
pdf.set_text_color(*PRIMARY)
pdf.cell(0, 14, "Focus IA", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 16)
pdf.set_text_color(*DARK)
pdf.cell(0, 10, "Guia para exponer el backend", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(20)
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(*GRAY)
pdf.multi_cell(
    0, 6,
    "Documento de referencia con las funciones, decisiones y endpoints "
    "mas importantes del backend. Pensado para defender en una exposicion: "
    "que hace cada cosa, por que esta asi, y como responder preguntas.",
    align="C", new_x="LMARGIN", new_y="NEXT",
)
pdf.ln(20)
pdf.set_fill_color(*LIGHT)
pdf.set_text_color(*DARK)
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 7, "  Stack tecnologico", fill=True, new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.set_fill_color(*LIGHT)
pdf.multi_cell(
    0, 6,
    "  FastAPI + SQLAlchemy async + fastapi-users + JWT\n"
    "  MySQL (Railway) + Alembic + Docker\n"
    "  Pydantic v2 para validacion en bordes",
    fill=True, new_x="LMARGIN", new_y="NEXT",
)

# ============== 1. ARQUITECTURA ==============
pdf.add_page()
pdf.h1("1. Arquitectura general")

pdf.body(
    "El backend es una API REST con FastAPI que sirve a tres clientes: "
    "el frontend Angular (panel del usuario), la extension Chrome (que monitorea "
    "distractores en tiempo real) y los tests psicometricos (TDAH e IQ)."
)

pdf.h2("Componentes clave")
pdf.bullet("app/main.py: configura el engine async, session factory, UserManager, JWT y CORS.")
pdf.bullet("app/models/: SQLAlchemy. User extiende SQLAlchemyBaseUserTable[int] (fastapi-users).")
pdf.bullet("app/schemas/: Pydantic v2. Validacion en los bordes (HTTP <-> dominio).")
pdf.bullet("app/routes/: routers por feature (preferences, sessions, tdah, iq, profile).")
pdf.bullet("app/services/profile.py: helpers compartidos (normalize_level, get_or_create_profile).")

pdf.h2("Por que async")
pdf.body(
    "La extension Chrome hace polling cada pocos segundos para saber si la "
    "sesion sigue activa, ademas de POSTear cada deteccion. Con SQLAlchemy "
    "async + aiomysql el servidor no bloquea hilos esperando la BD; un solo "
    "worker uvicorn maneja muchas conexiones concurrentes."
)

pdf.h2("Como hablar de auth")
pdf.body(
    "fastapi-users genera /auth/register, /auth/jwt/login, /users/me. El JWT se "
    "firma con JWT_SECRET (env var). Los routers propios protegen con la "
    "dependencia current_active_user."
)

# ============== 2. PATRONES ==============
pdf.add_page()
pdf.h1("2. Patrones que se repiten (los que mas preguntan)")

pdf.h2("2.1 Mutar User.profile_data (columna JSON)")
pdf.body(
    "SQLAlchemy NO detecta mutaciones in-place sobre columnas JSON. Si haces "
    "user.profile_data['x'] = 1 directamente, el ORM no marca el campo como "
    "dirty y el cambio no se guarda."
)
pdf.h3("Patron correcto:")
pdf.code(
    "data = dict(user.profile_data or {})  # 1. copia\n"
    "data['mode_alias'] = 'alerta'         # 2. muta la copia\n"
    "user.profile_data = data              # 3. asignacion (trigger ORM)\n"
    "flag_modified(user, 'profile_data')   # 4. seguro extra\n"
    "session.add(user)\n"
    "await session.commit()"
)
pdf.body(
    "Frase para defender: 'JSON en SQLAlchemy es opaco al ORM, hay que reasignar "
    "el dict y avisar con flag_modified'."
)

pdf.h2("2.2 Aliases vs niveles canonicos")
pdf.body(
    "El frontend muestra modos amigables (tranquilo / alerta / absoluta). "
    "La BD y la extension manejan niveles canonicos (bajo / intermedio / alto). "
    "Si no se mapea, el backend recibe 'alerta' y no lo reconoce -> "
    "todas las sesiones quedaban en 'intermedio' por default."
)
pdf.h3("Solucion en services/profile.py:")
pdf.code(
    "ALIAS_TO_LEVEL = {\n"
    "    'tranquilo': 'bajo',\n"
    "    'alerta':    'intermedio',\n"
    "    'absoluta':  'alto',\n"
    "}\n\n"
    "def normalize_level(value):\n"
    "    if not value: return None\n"
    "    v = value.strip().lower()\n"
    "    if v in VALID_LEVELS: return v\n"
    "    return ALIAS_TO_LEVEL.get(v)"
)

pdf.h2("2.3 Validacion en los bordes con Pydantic")
pdf.body(
    "En vez de validar dentro de la logica, se hace antes con Field(ge=, le=) "
    "y Literal[...]. Si llega algo invalido, FastAPI responde 422 antes de "
    "tocar BD."
)
pdf.code(
    "class IqAnswerIn(BaseModel):\n"
    "    questionId:    int = Field(..., ge=1, le=30)\n"
    "    selectedIndex: int = Field(..., ge=0, le=3)\n"
    "    timeSpentMs:   int = Field(..., ge=0)"
)

# ============== 3. ENDPOINTS ==============
pdf.add_page()
pdf.h1("3. Endpoints clave (con que decir de cada uno)")

pdf.h2("3.1 POST /preferences")
pdf.body("Guarda el modo y duracion preferidos del usuario.")
pdf.bullet("Recibe el alias del frontend (tranquilo/alerta/absoluta).")
pdf.bullet("Lo normaliza a canonico (bajo/intermedio/alto).")
pdf.bullet("Guarda alias en profile_data['mode_alias'] (para que el GET devuelva lo que el frontend espera).")
pdf.bullet("Actualiza PerfilEstudiante.nivel_restriccion (fuente de verdad para la extension).")
pdf.bullet("Si hay sesion activa, sincroniza Sesion.nivel_restriccion_sesion.")

pdf.h2("3.2 GET /sessions/active")
pdf.body(
    "Devuelve la sesion activa con el nivel VIVO (preferencia actual del perfil), "
    "no el snapshot con el que arranco la sesion. Asi, si el usuario cambia "
    "su modo a la mitad, la extension lo detecta sin reiniciar."
)
pdf.code(
    "perfil = await get_or_create_profile(session, user.id)\n"
    "nivel_vivo = (\n"
    "    perfil.nivel_restriccion\n"
    "    or sesion.nivel_restriccion_sesion\n"
    "    or 'intermedio'\n"
    ")"
)
pdf.body(
    "Importante: el snapshot Sesion.nivel_restriccion_sesion NO se borra. Solo "
    "se sincroniza desde POST /preferences. Asi los registros historicos de "
    "deteccion conservan el nivel real del momento."
)

pdf.h2("3.3 POST /tdah/resultados")
pdf.body(
    "Guarda el resultado del cuestionario TDAH (18 preguntas) en "
    "profile_data['tdah']. No se creo tabla porque solo interesa el "
    "ultimo resultado (YAGNI). Validacion estricta con Literal "
    "['Muy bajo','Bajo','Moderado','Alto','Muy alto']."
)

pdf.h2("3.4 POST /iq/resultados - la mas interesante de explicar")
pdf.body(
    "Hace tres cosas en UNA sola transaccion: guarda el resultado, ajusta "
    "preferencias automaticamente y sincroniza la sesion activa."
)
pdf.h3("Anti-trampa (el punto fuerte):")
pdf.body(
    "El frontend manda cada respuesta con un flag isCorrect, pero el backend "
    "lo IGNORA y recalcula el score contra una tabla autoritativa CORRECT_INDEX. "
    "Si el cliente manipula isCorrect, no afecta el resultado."
)
pdf.code(
    "score = 0\n"
    "for a in payload.answers:\n"
    "    if CORRECT_INDEX.get(a.questionId) == a.selectedIndex:\n"
    "        score += 1"
)
pdf.h3("Auto-ajuste de preferencias:")
pdf.code(
    "  < 40 % -> nivel Bajo      modo absoluta   25 min\n"
    " 40-70 % -> nivel Promedio  modo alerta     35 min\n"
    "  > 70 % -> nivel Alto      modo tranquilo  50 min"
)
pdf.body(
    "Logica: puntaje bajo necesita mas restriccion para concentrarse; puntaje "
    "alto ya autorregula bien, modo mas permisivo."
)

# ============== 4. PREGUNTAS Y RESPUESTAS ==============
pdf.add_page()
pdf.h1("4. Preguntas que pueden hacerte (y como responder)")
# normalizamos guiones largos por si quedo alguno

pdf.quote(
    "P: Por que guardas datos en JSON y no en columnas?",
    "Para datos que no quiero indexar ni consultar por ellos (mode_alias, "
    "duration, frases motivacionales, resultado de tests). Son del usuario, "
    "los lee solo el; no necesito JOINs ni WHEREs sobre esos campos. "
    "Crear tablas para todo seria sobreingenieria. Cuando algo necesite "
    "historial o filtros, ahi si migra a tabla.",
)

pdf.quote(
    "P: Por que el backend recalcula el score del IQ?",
    "Anti-trampa. El frontend manda isCorrect en cada respuesta, pero el "
    "cliente puede modificarlo. El backend tiene la tabla CORRECT_INDEX "
    "como fuente de verdad y siempre recalcula. Es defensa en profundidad.",
)

pdf.quote(
    "P: Por que /sessions/active devuelve el nivel del perfil y no el de la sesion?",
    "Para que los cambios de preferencia sean inmediatos sin tener que "
    "reiniciar la sesion. La extension hace polling y al siguiente tick ya "
    "tiene el nivel nuevo. El snapshot de la sesion sigue ahi para los "
    "registros historicos de deteccion.",
)

pdf.quote(
    "P: Que pasa si dos requests modifican profile_data al mismo tiempo?",
    "Cada request abre su propia sesion async. La ultima en commit gana "
    "(last write wins). Para los casos de uso actuales (un usuario, "
    "operaciones poco frecuentes) es aceptable. Si se vuelve critico se "
    "puede usar SELECT ... FOR UPDATE o version columns.",
)

pdf.quote(
    "P: Por que aliases en vez de mostrar bajo/intermedio/alto?",
    "UX. 'Modo tranquilo' comunica mejor que 'restriccion baja'. La "
    "separacion permite cambiar copys del frontend sin tocar logica de "
    "negocio ni la extension. El mapeo vive en un solo lugar (profile.py).",
)

pdf.quote(
    "P: Por que async y no sync?",
    "La extension Chrome hace polling y POSTea detecciones constantemente. "
    "Con sync, cada peticion bloquearia un thread esperando MySQL. Con async "
    "+ aiomysql, un solo worker uvicorn maneja muchas conexiones "
    "concurrentes sin escalar verticalmente.",
)

pdf.quote(
    "P: Por que fastapi-users en vez de tu propio auth?",
    "Da gratis: registro, login con JWT, password hashing con bcrypt, "
    "users/me, dependencias de proteccion de rutas. Lo unico que sobrescribi "
    "es _update del UserManager para soportar el campo username "
    "(que vive en profile_data, no es columna).",
)

# ============== 5. CHECKLIST EXPOSICION ==============
pdf.add_page()
pdf.h1("5. Mini-checklist para la exposicion")

pdf.h2("Que mencionar SI o SI")
pdf.bullet("Stack: FastAPI async + SQLAlchemy async + fastapi-users + JWT + MySQL.")
pdf.bullet("Patron de mutacion de columnas JSON (copia + reasignacion + flag_modified).")
pdf.bullet("Mapeo de aliases (era un bug: todas las sesiones quedaban en 'intermedio').")
pdf.bullet("Anti-trampa en el test de IQ (recalculo en backend con CORRECT_INDEX).")
pdf.bullet("Sesion con nivel vivo: preferencia se actualiza sin reiniciar sesion.")
pdf.bullet("Validacion en bordes con Pydantic (Field, Literal) -> 422 antes de tocar BD.")

pdf.h2("Frases listas para usar")
pdf.bullet(
    "'El backend es la fuente de verdad: aunque el frontend mande "
    "isCorrect, yo recalculo. Defensa en profundidad.'"
)
pdf.bullet(
    "'Aliases en frontend, niveles canonicos en BD. El mapeo vive en un "
    "solo lugar para no acoplar UI con logica de dominio.'"
)
pdf.bullet(
    "'Para columnas JSON en SQLAlchemy hay que reasignar el dict y avisar "
    "con flag_modified, sino el ORM no detecta el cambio.'"
)
pdf.bullet(
    "'Cuestionario TDAH guarda solo el ultimo resultado en JSON. Si en el "
    "futuro hace falta historial, se migra a tabla. YAGNI.'"
)

pdf.h2("Si te bloqueas")
pdf.body(
    "Vuelve siempre al diagrama: el backend recibe peticiones de frontend "
    "Angular y de la extension Chrome, valida en bordes con Pydantic, "
    "normaliza datos, opera en transacciones y guarda en MySQL. "
    "Todo lo demas son optimizaciones."
)

pdf.ln(6)
pdf.set_fill_color(*ACCENT)
pdf.set_text_color(255, 255, 255)
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 10, "  Suerte mañana. Tu lo entiendes mejor de lo que crees.", fill=True)

pdf.output(str(OUT))
print(f"PDF generado: {OUT}")
