"""Tesorería simulada · fuente de los bloqueos financieros (RN-BLO-01).

GET  /bloqueos/{estudiante_id}  -> consulta si el estudiante tiene bloqueo
PUT  /bloqueos/{estudiante_id}  -> activa o levanta un bloqueo (para los casos de prueba)
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import BaseModel

DB_URL = os.getenv("DATABASE_URL", "postgresql://matricula:matricula@localhost:5432/matricula")
pool = ConnectionPool(DB_URL, min_size=1, max_size=10, kwargs={"row_factory": dict_row}, open=False)


@asynccontextmanager
async def lifespan(_app):
    pool.open(wait=True, timeout=30)
    yield
    pool.close()


app = FastAPI(title="Tesorería simulada", version="1.0.0", lifespan=lifespan)


class Bloqueo(BaseModel):
    bloqueado: bool
    motivo: str | None = None


@app.get("/bloqueos/{estudiante_id}")
def consultar(estudiante_id: int):
    with pool.connection() as conn:
        r = conn.execute("SELECT bloqueado, motivo FROM tesoreria_bloqueos WHERE estudiante_id = %s",
                         (estudiante_id,)).fetchone()
    return {"estudiante_id": estudiante_id, "bloqueado": bool(r and r["bloqueado"]), "motivo": r["motivo"] if r else None}


@app.put("/bloqueos/{estudiante_id}")
def actualizar(estudiante_id: int, b: Bloqueo):
    with pool.connection() as conn:
        conn.execute("""INSERT INTO tesoreria_bloqueos (estudiante_id, bloqueado, motivo) VALUES (%s, %s, %s)
                        ON CONFLICT (estudiante_id) DO UPDATE SET bloqueado = EXCLUDED.bloqueado, motivo = EXCLUDED.motivo""",
                     (estudiante_id, b.bloqueado, b.motivo))
    return {"estudiante_id": estudiante_id, **b.model_dump()}
