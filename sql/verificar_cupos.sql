-- CP-CUP · RN-CUP-01: secciones con más inscritos que cupos (debe devolver 0 filas)
SELECT seccion_id, curso, numero, cupo, inscritos, inscritos - cupo AS sobrecupo
FROM v_ocupacion
WHERE inscritos > cupo
ORDER BY sobrecupo DESC;

-- Resumen para la evidencia de cada corrida
SELECT COUNT(*) FILTER (WHERE inscritos > cupo) AS secciones_con_sobrecupo,
       COALESCE(SUM(inscritos - cupo) FILTER (WHERE inscritos > cupo), 0) AS estudiantes_de_mas
FROM v_ocupacion;
