"""Generador de datos sintéticos para MatriculaRef (EDT 2.3.1 y 2.3.2).

Produce data/seed/seed.sql con:
  - Datos fijos para los casos de prueba (ver data/seed/FIXTURES.md).
  - Datos masivos ficticios con Faker: 2 000 estudiantes y 120 secciones para carga.

Uso:  python data/generar_datos.py
El archivo empieza con TRUNCATE, así que también sirve para reiniciar la base (EDT 2.3.3).
Ningún dato corresponde a personas reales.
"""
import random
from pathlib import Path

from faker import Faker

SEMILLA = 42
random.seed(SEMILLA)
fake = Faker("es_ES")
Faker.seed(SEMILLA)

cursos, prerreq, estudiantes, historial, secciones, horarios, inscripciones, tesoreria = [], [], [], [], [], [], [], []


def curso(codigo, nombre, creditos): cursos.append((codigo, nombre, creditos))
def req(c, r): prerreq.append((c, r))
def est(i, nombre=None, academico=False, maxc=18):
    estudiantes.append((i, f"A{i:06d}", nombre or fake.name(), academico, maxc))
def hist(e, c, estado): historial.append((e, c, estado))
def sec(i, c, num, cupo, franjas, abierta=True):
    secciones.append((i, c, num, cupo, abierta))
    for dia, ini, fin in franjas: horarios.append((i, dia, ini, fin))
def insc(e, s, estado="confirmada"): inscripciones.append((e, s, estado))
def teso(e, bloqueado, motivo): tesoreria.append((e, bloqueado, motivo))


# ---------------- Cursos fijos ----------------
curso("MAT101", "Cálculo I", 4)
curso("INF101", "Programación I", 4)
curso("INF102", "Programación II", 4);            req("INF102", "INF101")
curso("INF201", "Estructuras de Datos", 4);       req("INF201", "INF102")
curso("INF202", "Bases de Datos I", 4);           req("INF202", "INF102"); req("INF202", "MAT101")
curso("INF301", "Ingeniería de Software", 4);     req("INF301", "INF201")
for n in range(1, 41):                            # cursos generales para datos masivos
    curso(f"GEN{n:03d}", f"Curso general {n}", 3)
    if n > 20: req(f"GEN{n:03d}", f"GEN{n-20:03d}")
for n in range(80, 100):                          # cursos para casos de cupo, horario y límites
    curso(f"GEN{n:03d}", f"Curso de prueba {n}", 3)
for n, cr in [(201, 4), (202, 4), (203, 4), (204, 2), (205, 4), (206, 4)]:
    curso(f"CRD{n}", f"Curso de créditos {n}", cr)

# ---------------- Secciones fijas ----------------
sec(1, "INF101", 1, 1, [(1, "08:00", "10:00")])                 # último cupo
sec(2, "INF101", 2, 1, [(2, "08:00", "10:00")])                 # retiro + inscripción (llena)
for k in range(20):                                             # 20 secciones de 3 cupos
    sec(3 + k, f"GEN{80 + k % 10:03d}", 1 + k // 10, 3, [((k % 6) + 1, "18:00", "20:00")])
sec(30, "INF102", 1, 30, [(3, "08:00", "10:00")])
sec(31, "INF201", 1, 30, [(4, "08:00", "10:00")])
sec(32, "INF202", 1, 30, [(5, "08:00", "10:00")])
sec(33, "INF301", 1, 30, [(6, "08:00", "10:00")])
sec(40, "GEN090", 1, 30, [(1, "13:00", "15:00")])               # base para choques
sec(41, "GEN091", 1, 30, [(1, "13:00", "15:00")])               # mismo inicio (choque total)
sec(42, "GEN092", 1, 30, [(1, "14:00", "16:00")])               # inicia dentro (parcial)
sec(43, "GEN093", 1, 30, [(1, "12:00", "14:00")])               # inicia antes (parcial)
sec(44, "GEN094", 1, 30, [(1, "13:30", "14:30")])               # contenido
sec(45, "GEN095", 1, 30, [(1, "15:00", "17:00")])               # contiguo: NO es choque
sec(46, "GEN096", 1, 30, [(2, "13:00", "15:00")])               # otro día: NO es choque
sec(47, "GEN097", 1, 30, [(1, "11:00", "17:00")])               # contiene a la base
sec(50, "GEN098", 1, 30, [(3, "13:00", "15:00")], abierta=False)  # sección cerrada
sec(51, "GEN099", 1, 0, [(4, "13:00", "15:00")])                # sin cupo
for k, c in enumerate(["CRD201", "CRD202", "CRD203", "CRD204", "CRD205"]):
    sec(60 + k, c, 1, 30, [(6, f"{10 + 2*k:02d}:00", f"{11 + 2*k:02d}:00")])
sec(65, "CRD206", 1, 30, [(5, "18:00", "20:00")])               # +4 créditos

# ---------------- Estudiantes fijos ----------------
for i in range(1001, 1301): est(i)                              # 300 para concurrencia
est(1500); insc(1500, 2)                                        # ocupa el único cupo de la sección 2
est(2001); hist(2001, "INF101", "aprobado")
est(2002); hist(2002, "INF101", "reprobado")
est(2003)
est(2004); hist(2004, "INF101", "en_curso")
est(2005); hist(2005, "INF102", "aprobado")
est(2006); hist(2006, "INF102", "aprobado"); hist(2006, "MAT101", "aprobado")
est(2007); [hist(2007, c, "aprobado") for c in ("INF101", "INF102")]; hist(2007, "INF201", "en_curso")
est(2008); [hist(2008, c, "aprobado") for c in ("INF101", "INF102", "INF201")]
for i in range(3001, 3011): est(i)                              # choques de horario
est(4001); teso(4001, True, "Saldo pendiente")
est(4002, academico=True)
est(4003, academico=True); teso(4003, True, "Saldo pendiente")
est(4004); teso(4004, False, "Bloqueo levantado")
est(4005)                                                       # se bloquea durante la prueba
est(5001); [insc(5001, s) for s in (60, 61, 62, 63)]            # 4+4+4+2 = 14 créditos
est(5002); [insc(5002, s) for s in (60, 61, 62, 64)]            # 4+4+4+4 = 16 créditos

# ---------------- Datos masivos ----------------
franjas = [(d, f"{h:02d}:00", f"{h+2:02d}:00") for d in range(1, 7) for h in (7, 9, 11, 13, 15, 17, 19)]
sid = 100
for n in range(1, 41):
    for num in (1, 2, 3):
        sec(sid, f"GEN{n:03d}", num, random.randint(25, 40), [random.choice(franjas)]); sid += 1
for i in range(10001, 12001):
    est(i, academico=random.random() < 0.02)
    for n in random.sample(range(1, 21), random.randint(0, 6)):
        hist(i, f"GEN{n:03d}", random.choices(["aprobado", "reprobado", "en_curso"], [0.75, 0.15, 0.10])[0])
    if random.random() < 0.05: teso(i, True, "Saldo pendiente")


# ---------------- Escritura ----------------
def v(x):
    if isinstance(x, bool): return "TRUE" if x else "FALSE"
    if isinstance(x, int): return str(x)
    return "'" + str(x).replace("'", "''") + "'"


def inserts(tabla, cols, filas, lote=500):
    out = []
    for k in range(0, len(filas), lote):
        vals = ",\n".join("(" + ", ".join(v(x) for x in f) + ")" for f in filas[k:k + lote])
        out.append(f"INSERT INTO {tabla} ({', '.join(cols)}) VALUES\n{vals};")
    return "\n".join(out)


sql = [
    "-- Generado por data/generar_datos.py (semilla %d). No editar a mano." % SEMILLA,
    "TRUNCATE inscripciones, horarios, secciones, historial, prerrequisitos, tesoreria_bloqueos, estudiantes, cursos RESTART IDENTITY CASCADE;",
    inserts("cursos", ["codigo", "nombre", "creditos"], cursos),
    inserts("prerrequisitos", ["curso", "requisito"], prerreq),
    inserts("estudiantes", ["id", "carne", "nombre", "bloqueo_academico", "max_creditos"], estudiantes),
    inserts("historial", ["estudiante_id", "curso", "estado"], historial),
    inserts("secciones", ["id", "curso", "numero", "cupo", "abierta"], secciones),
    inserts("horarios", ["seccion_id", "dia", "inicio", "fin"], horarios),
    inserts("inscripciones", ["estudiante_id", "seccion_id", "estado"], inscripciones),
    inserts("tesoreria_bloqueos", ["estudiante_id", "bloqueado", "motivo"], tesoreria),
]
destino = Path(__file__).parent / "seed" / "seed.sql"
destino.parent.mkdir(exist_ok=True)
destino.write_text("\n\n".join(sql) + "\n", encoding="utf-8")
print(f"{destino}: {len(estudiantes)} estudiantes, {len(secciones)} secciones, {len(cursos)} cursos")
