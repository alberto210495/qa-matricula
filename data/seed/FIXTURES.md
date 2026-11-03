# Datos fijos para los casos de prueba

Generados por `data/generar_datos.py` (semilla 42). Reinicien la base antes de cada caso o corrida con `data/reset.ps1`.

## Secciones

| ID | Curso | Cupo | Horario | Uso |
|---|---|---|---|---|
| 1 | INF101 Programación I | 1 | Lun 08:00–10:00 | Último cupo (CP-CUP-01 a 04) |
| 2 | INF101 Programación I | 1 (ocupado por el estudiante 1500) | Mar 08:00–10:00 | Retiro e inscripción simultáneos (CP-CUP-05) |
| 3–22 | GEN080–GEN089 | 3 cada una | 18:00–20:00 | 20 secciones de 3 cupos (CP-CUP-06) |
| 30 | INF102 (requiere INF101) | 30 | Mié 08:00–10:00 | Prerrequisitos |
| 31 | INF201 (requiere INF102) | 30 | Jue 08:00–10:00 | Cadena de prerrequisitos |
| 32 | INF202 (requiere INF102 y MAT101) | 30 | Vie 08:00–10:00 | Varios prerrequisitos |
| 33 | INF301 (requiere INF201) | 30 | Sáb 08:00–10:00 | Cadena INF101 → INF102 → INF201 → INF301 |
| 40 | GEN090 | 30 | Lun 13:00–15:00 | Base para choques de horario |
| 41 | GEN091 | 30 | Lun 13:00–15:00 | Mismo horario → choque |
| 42 | GEN092 | 30 | Lun 14:00–16:00 | Inicia dentro de la base → choque |
| 43 | GEN093 | 30 | Lun 12:00–14:00 | Inicia antes y se traslapa → choque |
| 44 | GEN094 | 30 | Lun 13:30–14:30 | Contenido en la base → choque |
| 45 | GEN095 | 30 | Lun 15:00–17:00 | Contiguo → **no** es choque |
| 46 | GEN096 | 30 | Mar 13:00–15:00 | Otro día → **no** es choque |
| 47 | GEN097 | 30 | Lun 11:00–17:00 | Contiene a la base → choque |
| 50 | GEN098 | 30, cerrada | Mié 13:00–15:00 | Sección cerrada (RN-LIM-02) |
| 51 | GEN099 | 0 | Jue 13:00–15:00 | Sin cupo (RN-LIM-02) |
| 65 | CRD206 (4 créditos) | 30 | Vie 18:00–20:00 | Límite de créditos |
| 100–219 | GEN001–GEN040 | 25–40 | Varios | Datos masivos para carga |

## Estudiantes

| ID | Situación | Uso |
|---|---|---|
| 1001–1300 | Sin historial ni bloqueos | Concurrencia y carga (300 usuarios) |
| 1500 | Tiene el único cupo de la sección 2 | Retiro simultáneo |
| 2001 | INF101 aprobado | Puede matricular INF102 |
| 2002 | INF101 reprobado | No puede matricular INF102 |
| 2003 | Sin historial | No puede matricular INF102 |
| 2004 | INF101 en curso | No puede matricular INF102 |
| 2005 | INF102 aprobado, MAT101 no | No puede matricular INF202 |
| 2006 | INF102 y MAT101 aprobados | Puede matricular INF202 |
| 2007 | INF101 e INF102 aprobados, INF201 en curso | No puede matricular INF301 |
| 2008 | INF101, INF102 e INF201 aprobados | Puede matricular INF301 |
| 3001–3010 | Sin restricciones | Choques de horario (primero la sección 40, luego la otra) |
| 4001 | Bloqueo financiero activo | RN-BLO-01 |
| 4002 | Bloqueo académico activo | RN-BLO-02 |
| 4003 | Ambos bloqueos | RN-BLO-01 y 02 |
| 4004 | Bloqueo financiero levantado | Debe poder matricular y confirmar |
| 4005 | Sin bloqueo | Bloqueo aplicado a mitad de la matrícula (RN-BLO-03) |
| 5001 | 14 créditos confirmados | +4 créditos = 18 → se permite |
| 5002 | 16 créditos confirmados | +4 créditos = 20 → se rechaza |
| 10001–12000 | Datos ficticios con Faker (5 % con bloqueo financiero, 2 % académico) | Carga |

## Cómo aplicar un bloqueo a mitad de la matrícula (CP-BLO-05)

1. Inscribir al estudiante 4005 en una sección (`POST /inscripciones`).
2. Activar el bloqueo en Tesorería: `PUT http://localhost:8001/bloqueos/4005` con `{"bloqueado": true, "motivo": "prueba"}`.
3. Confirmar: `POST /estudiantes/4005/confirmar`. Resultado esperado: 409 `RN-BLO-03` y los cupos apartados liberados.
