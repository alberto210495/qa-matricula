-- Verificaciones de integridad después de cada sesión de pruebas. Cada consulta debe devolver 0 filas.

-- 1. RN-CUP-01: sobrecupo
SELECT 'sobrecupo' AS falla, seccion_id::text AS detalle FROM v_ocupacion WHERE inscritos > cupo
UNION ALL
-- 2. RN-PRE-01..03: inscripciones activas sin prerrequisitos aprobados
SELECT 'prerrequisito', i.id::text
FROM inscripciones i JOIN secciones s ON s.id = i.seccion_id JOIN prerrequisitos p ON p.curso = s.curso
LEFT JOIN historial h ON h.estudiante_id = i.estudiante_id AND h.curso = p.requisito
WHERE i.estado <> 'retirada' AND (h.estado IS NULL OR h.estado <> 'aprobado')
UNION ALL
-- 3. RN-HOR-01: choques entre inscripciones activas del mismo estudiante
SELECT 'choque_horario', a.id::text || ' vs ' || b.id::text
FROM inscripciones a JOIN inscripciones b ON a.estudiante_id = b.estudiante_id AND a.id < b.id
JOIN horarios ha ON ha.seccion_id = a.seccion_id JOIN horarios hb ON hb.seccion_id = b.seccion_id
WHERE a.estado <> 'retirada' AND b.estado <> 'retirada'
  AND ha.dia = hb.dia AND ha.inicio < hb.fin AND ha.fin > hb.inicio
UNION ALL
-- 4. RN-BLO-01..02: matrículas confirmadas con bloqueo activo
SELECT 'confirmada_con_bloqueo', i.id::text
FROM inscripciones i JOIN estudiantes e ON e.id = i.estudiante_id
LEFT JOIN tesoreria_bloqueos t ON t.estudiante_id = e.id
WHERE i.estado = 'confirmada' AND (e.bloqueo_academico OR COALESCE(t.bloqueado, FALSE))
UNION ALL
-- 5. RN-LIM-01: estudiantes por encima del máximo de créditos
SELECT 'exceso_creditos', e.id::text
FROM estudiantes e JOIN inscripciones i ON i.estudiante_id = e.id AND i.estado <> 'retirada'
JOIN secciones s ON s.id = i.seccion_id JOIN cursos c ON c.codigo = s.curso
GROUP BY e.id, e.max_creditos HAVING SUM(c.creditos) > e.max_creditos;
