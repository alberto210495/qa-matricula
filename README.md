# QA Matrícula Universitaria · Grupo 7

Proyecto final del curso **Pruebas de aseguramiento de la calidad del software** (ULACIT).
Estrategia de pruebas para el sistema de matrícula de la Universidad de Referencia (caso de estudio): integridad de cupos bajo concurrencia, prerrequisitos, choques de horario, bloqueos financieros y académicos, y rendimiento.

- **Documento vigente:** [`docs/Avance_II_Grupo7_v2.0.docx`](docs/Avance_II_Grupo7_v2.0.docx)
- **Tablero de Jira:** https://albertoleon2104-1791760045786.atlassian.net/jira/software/projects/SCRUM/boards/1
- **Profesor:** Clarence Ricketts Torres

## Equipo

| Integrante | Rol |
|---|---|
| Antonio Pacheco Acosta | Gerente del proyecto / Líder de QA |
| Fabricio Solis Redondo | Analista de pruebas |
| Alberto León Rojas | Automatización y rendimiento |
| Marco Gomez Pavon | Ejecución y registro de defectos |

## Estructura

| Carpeta | Contenido |
|---|---|
| `docs/` | Acta, EDT, plan de pruebas, informes y diagramas |
| `sut/` | Sistema bajo prueba MatriculaRef (una etiqueta de Git por versión) |
| `tests/k6/` | Scripts de concurrencia, carga y estrés |
| `sql/` | Consultas de verificación (inscritos ≤ cupo, coherencia) |
| `data/` | Generador de datos sintéticos (Python + Faker) y datos base |
| `docker/` | `docker-compose.yml` del ambiente de pruebas |
| `evidencias/` | Resultados de k6, capturas y pruebas de humo |

## Control de versiones del documento

Solo el líder de QA publica versiones nuevas del documento en `docs/`, cada una con una etiqueta de Git (`doc-v2.0`, `doc-v2.1`…). Cada integrante entrega el archivo descargado de esa etiqueta, de modo que todos los envíos sean idénticos.

## Ejecución (cuando MatriculaRef v1.0.0 esté disponible)

```bash
cd docker
docker compose up -d        # levanta API, base de datos y Tesorería simulada
k6 run ../tests/k6/smoke.js # prueba de humo antes de cada sesión
```

> Todos los datos son ficticios. No se usan datos reales de estudiantes.
