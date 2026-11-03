# Diferencias entre el ambiente de pruebas y producción

**Historia:** SCRUM-18 · **EDT:** 2.2.1 · 2.2.2 · **Riesgo que mitiga:** R1 (el ambiente de pruebas no representa producción)
**Versión del ambiente:** MatriculaRef v1.0.0 · `docker/docker-compose.yml`

El ambiente de pruebas corre en una sola computadora con Docker. Reproduce las reglas de negocio y la arquitectura lógica del sistema de matrícula (API, base de datos y Tesorería), pero no la infraestructura de producción. Esta tabla deja claro qué resultados se pueden trasladar a producción y cuáles no.

| Aspecto | Producción (sistema de la universidad) | Ambiente de pruebas | Efecto en los resultados |
|---|---|---|---|
| Infraestructura | Servidores dedicados, posiblemente varias instancias detrás de un balanceador | Tres contenedores en una sola máquina (Docker Desktop) | Los tiempos absolutos no se trasladan a producción; sirven para comparar versiones en las mismas condiciones. |
| Instancias de la API | Una o más, según la configuración institucional | Una sola instancia de FastAPI con un proceso de uvicorn | La concurrencia real entre servidores no se reproduce; sí la concurrencia sobre la base de datos, que es donde se origina el sobrecupo. |
| Base de datos | Motor y configuración institucionales, con respaldos y réplicas | PostgreSQL 16 con la configuración por defecto | Las reglas de integridad se prueban igual; el rendimiento de la base depende del hardware local. |
| Conexiones a la base | Dimensionadas por TI | Grupo de 20 conexiones en la API (`DB_POOL_MAX`) y 10 en Tesorería | Con más de 20 usuarios simultáneos las solicitudes esperan turno; se tiene en cuenta al interpretar la carga. |
| Tesorería | Sistema financiero real, con su propia latencia y disponibilidad | Servicio simulado sobre la misma base de datos | No se mide la latencia real de Tesorería; los bloqueos se activan a voluntad (`PUT /bloqueos/{id}`) para cubrir cada caso. |
| Interfaz de usuario | Portal web de matrícula | Sin portal web; se usa la API directamente y la documentación interactiva de Swagger (`/docs`) | Las pruebas validan reglas y rendimiento del servidor; la usabilidad del portal queda fuera del alcance. |
| Datos | Estudiantes, historiales y oferta reales | Datos sintéticos generados con Faker (semilla 42): unas 2 300 personas estudiantes y 160 secciones con casos fijos | No hay datos personales reales; el volumen es menor al de producción. |
| Red | Usuarios conectados por internet, con latencia variable | Todo en `localhost` | Los tiempos medidos no incluyen la red; los umbrales se interpretan como tiempo del servidor. |
| Seguridad | Autenticación institucional, HTTPS | Sin autenticación ni HTTPS | No se prueban la autenticación ni el cifrado. |
| Estado entre corridas | Datos acumulados durante todo el periodo de matrícula | La base se reinicia antes de cada corrida (`data/reset.ps1`) | Cada corrida arranca en el mismo estado, así que los resultados se pueden repetir y comparar. |

## Lo que sí se puede concluir

- **Reglas de negocio** (cupos, prerrequisitos, horarios, bloqueos y créditos): los resultados aplican a producción, porque la lógica que se prueba es la misma.
- **Integridad bajo concurrencia:** un sobrecupo detectado aquí también puede darse en producción, ya que depende de cómo la transacción bloquea la sección y no del hardware.
- **Rendimiento:** solo sirve para comparar versiones en el mismo equipo. Para trasladarlo a producción se necesita una corrida en un ambiente equivalente, que debe coordinarse con TI.

## Equipo donde se ejecuta la carga

| Dato | Valor |
|---|---|
| Procesador | [modelo] |
| Memoria | [GB de RAM] |
| Sistema operativo | Windows [versión] con Docker Desktop [versión] |
| k6 | [versión] |

Se completa en cada informe de rendimiento para que la corrida se pueda reproducir.
