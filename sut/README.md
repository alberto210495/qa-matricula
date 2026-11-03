# MatriculaRef v1.0.0

Sistema de matrícula de referencia de la Universidad de Referencia (caso de estudio). Es el sistema bajo prueba del proyecto; lo suministra el Equipo de desarrollo (TI).

## Componentes

| Servicio | Puerto | Descripción |
|---|---|---|
| `api` | 8000 | API REST de matrícula (Python, FastAPI). Documentación interactiva en http://localhost:8000/docs |
| `tesoreria` | 8001 | Tesorería simulada: fuente de los bloqueos financieros |
| `db` | 5432 | PostgreSQL 16 (usuario, contraseña y base: `matricula`) |

## Levantar el ambiente

Requisitos: Docker Desktop en ejecución.

```powershell
cd docker
docker compose up -d --build
```

La primera vez descarga las imágenes y carga los datos (1–2 minutos). Luego, desde la raíz del repositorio:

```powershell
k6 run tests/k6/smoke.js          # prueba de humo: todas las verificaciones deben pasar
```

Comandos útiles:

```powershell
docker compose -f docker/docker-compose.yml logs -f api   # ver el registro de la API
.\data\reset.ps1                                          # reiniciar los datos (antes de cada corrida)
docker compose -f docker/docker-compose.yml down -v       # apagar y borrar la base
```

## Endpoints

| Método | Ruta | Regla |
|---|---|---|
| GET | `/salud` | Disponibilidad y versión |
| GET | `/oferta?curso=INF101` | Secciones con cupo disponible y horario |
| GET | `/estudiantes/{id}/matricula` | Inscripciones activas y créditos |
| POST | `/inscripciones` `{"estudiante_id", "seccion_id"}` | Cupo, prerrequisitos, horario, créditos y bloqueos |
| DELETE | `/inscripciones/{id}` | Retiro (libera el cupo) |
| POST | `/estudiantes/{id}/confirmar` | Confirmación (revalida bloqueos) |
| POST | `/estudiantes/{id}/cancelar` | Cancela el proceso y libera los cupos apartados |

Cada rechazo responde **409** con el código de la regla incumplida, por ejemplo:

```json
{"detail": {"codigo": "RN-CUP-01", "mensaje": "La sección no tiene cupos disponibles."}}
```

Códigos posibles: `RN-CUP-01`, `RN-PRE-01`, `RN-HOR-01`, `RN-BLO-01`, `RN-BLO-02`, `RN-BLO-03`, `RN-LIM-01`, `RN-LIM-02`, `DUPLICADA`, `SIN_INSCRIPCIONES`.

Los datos fijos para cada caso de prueba están en [`data/seed/FIXTURES.md`](../data/seed/FIXTURES.md).

## Versiones

Cada entrega se etiqueta en Git (`v1.0.0`, `v1.0.1`, …). Las correcciones de defectos se publican como versiones nuevas con sus notas.
