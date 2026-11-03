# Notas del rol de TI (no leer si diseñan o ejecutan casos de prueba)

La versión 1.0.0 reproduce las fallas que el acta describe para el sistema actual, para que la estrategia de pruebas tenga defectos reales que detectar. Se controlan con la variable `MODO_DEFECTOS` del `docker-compose.yml`:

- `MODO_DEFECTOS=1` (por defecto en v1.0.0): sistema con las fallas del acta.
- `MODO_DEFECTOS=0`: reglas corregidas. Es el comportamiento que se entrega como corrección (v1.0.1) cuando QA reporta cada defecto.

| Falla del acta | Comportamiento en v1.0.0 | Corrección |
|---|---|---|
| Integridad de cupos | Cuenta los cupos y luego inserta sin bloquear la sección; con solicitudes simultáneas se asigna el mismo cupo a varios estudiantes. | `SELECT … FOR UPDATE` sobre la sección dentro de la transacción. |
| Prerrequisitos | Acepta un prerrequisito «en curso» como si estuviera aprobado. | Solo cuenta el estado `aprobado`. |
| Choques de horario | Solo detecta el choque si el curso nuevo empieza dentro del existente; no detecta los que empiezan antes y se traslapan, ni los que lo contienen. | Traslape real: `inicio_nuevo < fin_existente` y `fin_nuevo > inicio_existente`. |
| Bloqueos | Valida los bloqueos solo al inscribir; si se aplica un bloqueo después, la confirmación lo deja pasar. | Revalidar bloqueos al confirmar y liberar los cupos apartados. |

Cuando QA reporte un defecto en Jira, la corrección se entrega cambiando la variable a `0` (o corrigiendo la regla puntual en `app/main.py`), con una etiqueta nueva en Git y notas de la versión.
