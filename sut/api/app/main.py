"""MatriculaRef · API de matrícula (sistema bajo prueba del proyecto de QA, Grupo 7).

Implementa el catálogo de reglas de negocio del Anexo B. Cada rechazo devuelve el código
de la regla incumplida, para que los casos de prueba puedan verificarlo.
"""
import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field

VERSION = "1.0.0"
DB_URL = os.getenv("DATABASE_URL", "postgresql://matricula:matricula@localhost:5432/matricula")
TESORERIA_URL = os.getenv("TESORERIA_URL", "http://localhost:8001")
# Reproduce las fallas descritas en el acta (ver sut/NOTAS_TI.md). Se desactiva en v1.0.1+.
MODO_DEFECTOS = os.getenv("MODO_DEFECTOS", "1") == "1"

http = httpx.Client(base_url=TESORERIA_URL, timeout=3, limits=httpx.Limits(max_connections=50, max_keepalive_connections=50))
pool = ConnectionPool(DB_URL, min_size=2, max_size=int(os.getenv("DB_POOL_MAX", "20")),
                      kwargs={"row_factory": dict_row}, open=False)


@asynccontextmanager
async def lifespan(_app):
    pool.open(wait=True, timeout=30)
    yield
    pool.close()
    http.close()


app = FastAPI(
    title="MatriculaRef",
    version=VERSION,
    description="Sistema de matrícula de referencia de la Universidad de Referencia (caso de estudio). "
                "Usa esta página para la ejecución manual de los casos de prueba.",
    lifespan=lifespan,
)


class SolicitudInscripcion(BaseModel):
    estudiante_id: int = Field(..., examples=[1001])
    seccion_id: int = Field(..., examples=[1])


def rechazo(status: int, codigo: str, mensaje: str):
    raise HTTPException(status_code=status, detail={"codigo": codigo, "mensaje": mensaje})


def bloqueo_financiero(estudiante_id: int) -> bool:
    try:
        r = http.get(f"/bloqueos/{estudiante_id}")
        r.raise_for_status()
        return bool(r.json()["bloqueado"])
    except httpx.HTTPError:
        rechazo(503, "TESORERIA_NO_DISPONIBLE", "No se pudo consultar Tesorería; intente de nuevo.")


def choca(nuevo, existente) -> bool:
    if nuevo["dia"] != existente["dia"]:
        return False
    if MODO_DEFECTOS:
        # Solo detecta el choque si el curso nuevo empieza dentro del existente.
        return existente["inicio"] <= nuevo["inicio"] < existente["fin"]
    # Traslape real; dos bloques contiguos (uno termina cuando el otro inicia) no chocan.
    return nuevo["inicio"] < existente["fin"] and nuevo["fin"] > existente["inicio"]


def horarios_de(cur, seccion_ids):
    if not seccion_ids:
        return []
    cur.execute("SELECT seccion_id, dia, inicio, fin FROM horarios WHERE seccion_id = ANY(%s)", (list(seccion_ids),))
    return cur.fetchall()


@app.get("/salud", tags=["Sistema"])
def salud():
    with pool.connection() as conn:
        conn.execute("SELECT 1")
    return {"estado": "ok", "version": VERSION}


@app.get("/oferta", tags=["Consulta"])
def oferta(curso: str | None = None):
    sql = """SELECT o.seccion_id, o.curso, c.nombre, c.creditos, o.numero, o.cupo, o.inscritos,
                    GREATEST(o.cupo - o.inscritos, 0) AS disponibles, s.abierta
             FROM v_ocupacion o JOIN cursos c ON c.codigo = o.curso JOIN secciones s ON s.id = o.seccion_id
             WHERE (%(curso)s::text IS NULL OR o.curso = %(curso)s) ORDER BY o.seccion_id"""
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql, {"curso": curso})
        secciones = cur.fetchall()
        hs = horarios_de(cur, [s["seccion_id"] for s in secciones])
    por_seccion = {}
    for h in hs:
        por_seccion.setdefault(h["seccion_id"], []).append(
            {"dia": h["dia"], "inicio": h["inicio"].strftime("%H:%M"), "fin": h["fin"].strftime("%H:%M")})
    for s in secciones:
        s["horarios"] = por_seccion.get(s["seccion_id"], [])
    return secciones


@app.get("/estudiantes/{estudiante_id}/matricula", tags=["Consulta"])
def ver_matricula(estudiante_id: int):
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, carne, nombre FROM estudiantes WHERE id = %s", (estudiante_id,))
        est = cur.fetchone()
        if not est:
            rechazo(404, "ESTUDIANTE_NO_EXISTE", "El estudiante no existe.")
        cur.execute("""SELECT i.id AS inscripcion_id, i.estado, s.id AS seccion_id, s.curso, s.numero, c.creditos
                       FROM inscripciones i JOIN secciones s ON s.id = i.seccion_id JOIN cursos c ON c.codigo = s.curso
                       WHERE i.estudiante_id = %s AND i.estado <> 'retirada' ORDER BY i.id""", (estudiante_id,))
        inscripciones = cur.fetchall()
    return {**est, "creditos": sum(i["creditos"] for i in inscripciones), "inscripciones": inscripciones}


@app.post("/inscripciones", status_code=201, tags=["Matrícula"])
def inscribir(sol: SolicitudInscripcion):
    with pool.connection() as conn:
        est = conn.execute("SELECT * FROM estudiantes WHERE id = %s", (sol.estudiante_id,)).fetchone()
    if not est:
        rechazo(404, "ESTUDIANTE_NO_EXISTE", "El estudiante no existe.")
    if est["bloqueo_academico"]:
        rechazo(409, "RN-BLO-02", "El estudiante tiene un bloqueo académico activo.")
    if bloqueo_financiero(sol.estudiante_id):
        rechazo(409, "RN-BLO-01", "El estudiante tiene un bloqueo financiero activo en Tesorería.")

    with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        bloqueo = "" if MODO_DEFECTOS else " FOR UPDATE"
        cur.execute(f"""SELECT s.*, c.creditos FROM secciones s JOIN cursos c ON c.codigo = s.curso
                        WHERE s.id = %s{bloqueo}""", (sol.seccion_id,))
        sec = cur.fetchone()
        if not sec:
            rechazo(404, "SECCION_NO_EXISTE", "La sección no existe.")
        if not sec["abierta"]:
            rechazo(409, "RN-LIM-02", "La sección está cerrada.")

        cur.execute("""SELECT 1 FROM inscripciones i JOIN secciones s ON s.id = i.seccion_id
                       WHERE i.estudiante_id = %s AND s.curso = %s AND i.estado <> 'retirada'""",
                    (sol.estudiante_id, sec["curso"]))
        if cur.fetchone():
            rechazo(409, "DUPLICADA", "El estudiante ya tiene una sección activa de este curso.")

        # Prerrequisitos (RN-PRE-01 a 03)
        cur.execute("""SELECT p.requisito, h.estado FROM prerrequisitos p
                       LEFT JOIN historial h ON h.curso = p.requisito AND h.estudiante_id = %s
                       WHERE p.curso = %s""", (sol.estudiante_id, sec["curso"]))
        validos = {"aprobado", "en_curso"} if MODO_DEFECTOS else {"aprobado"}
        faltantes = [r["requisito"] for r in cur.fetchall() if r["estado"] not in validos]
        if faltantes:
            rechazo(409, "RN-PRE-01", f"Prerrequisitos no aprobados: {', '.join(faltantes)}.")

        # Horario (RN-HOR-01 y 02) y créditos (RN-LIM-01)
        cur.execute("""SELECT i.seccion_id, c.creditos FROM inscripciones i
                       JOIN secciones s ON s.id = i.seccion_id JOIN cursos c ON c.codigo = s.curso
                       WHERE i.estudiante_id = %s AND i.estado <> 'retirada'""", (sol.estudiante_id,))
        actuales = cur.fetchall()
        nuevos = horarios_de(cur, [sol.seccion_id])
        existentes = horarios_de(cur, [a["seccion_id"] for a in actuales])
        for n in nuevos:
            for e in existentes:
                if choca(n, e):
                    rechazo(409, "RN-HOR-01", f"Choque de horario con la sección {e['seccion_id']}.")
        total = sum(a["creditos"] for a in actuales) + sec["creditos"]
        if total > est["max_creditos"]:
            rechazo(409, "RN-LIM-01", f"Supera el máximo de {est['max_creditos']} créditos ({total}).")

        # Cupo (RN-CUP-01 y RN-LIM-02)
        cur.execute("SELECT COUNT(*) AS n FROM inscripciones WHERE seccion_id = %s AND estado IN ('apartada','confirmada')",
                    (sol.seccion_id,))
        ocupados = cur.fetchone()["n"]
        if MODO_DEFECTOS:
            time.sleep(0.3)  # validación externa simulada entre la lectura y la escritura
        if ocupados >= sec["cupo"]:
            rechazo(409, "RN-CUP-01", "La sección no tiene cupos disponibles.")

        cur.execute("""INSERT INTO inscripciones (estudiante_id, seccion_id, estado)
                       VALUES (%s, %s, 'apartada') RETURNING id, estado""", (sol.estudiante_id, sol.seccion_id))
        nueva = cur.fetchone()
    return {"inscripcion_id": nueva["id"], "estado": nueva["estado"], "seccion_id": sol.seccion_id}


@app.delete("/inscripciones/{inscripcion_id}", tags=["Matrícula"])
def retirar(inscripcion_id: int):
    with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        cur.execute("""UPDATE inscripciones SET estado = 'retirada', actualizada = now()
                       WHERE id = %s AND estado <> 'retirada' RETURNING id, seccion_id""", (inscripcion_id,))
        r = cur.fetchone()
    if not r:
        rechazo(404, "INSCRIPCION_NO_EXISTE", "La inscripción no existe o ya fue retirada.")
    return {"inscripcion_id": r["id"], "estado": "retirada", "cupo_liberado_en_seccion": r["seccion_id"]}


@app.post("/estudiantes/{estudiante_id}/confirmar", tags=["Matrícula"])
def confirmar(estudiante_id: int):
    with pool.connection() as conn:
        est = conn.execute("SELECT * FROM estudiantes WHERE id = %s", (estudiante_id,)).fetchone()
    if not est:
        rechazo(404, "ESTUDIANTE_NO_EXISTE", "El estudiante no existe.")

    if not MODO_DEFECTOS:
        # RN-BLO-03: los bloqueos se vuelven a validar al confirmar
        motivo = None
        if est["bloqueo_academico"]:
            motivo = ("RN-BLO-02", "bloqueo académico")
        elif bloqueo_financiero(estudiante_id):
            motivo = ("RN-BLO-01", "bloqueo financiero")
        if motivo:
            with pool.connection() as conn:
                conn.execute("""UPDATE inscripciones SET estado = 'retirada', actualizada = now()
                                WHERE estudiante_id = %s AND estado = 'apartada'""", (estudiante_id,))
            rechazo(409, "RN-BLO-03", f"No se puede confirmar: {motivo[1]} activo. Se liberaron los cupos apartados.")

    with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        cur.execute("""UPDATE inscripciones SET estado = 'confirmada', actualizada = now()
                       WHERE estudiante_id = %s AND estado = 'apartada' RETURNING id""", (estudiante_id,))
        confirmadas = [r["id"] for r in cur.fetchall()]
    if not confirmadas:
        rechazo(409, "SIN_INSCRIPCIONES", "No hay inscripciones apartadas para confirmar.")
    return {"estudiante_id": estudiante_id, "confirmadas": confirmadas}


@app.post("/estudiantes/{estudiante_id}/cancelar", tags=["Matrícula"])
def cancelar(estudiante_id: int):
    """RN-LIM-03: cancelar el proceso libera los cupos apartados."""
    with pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
        cur.execute("""UPDATE inscripciones SET estado = 'retirada', actualizada = now()
                       WHERE estudiante_id = %s AND estado = 'apartada' RETURNING id""", (estudiante_id,))
        liberadas = [r["id"] for r in cur.fetchall()]
    return {"estudiante_id": estudiante_id, "liberadas": liberadas}
