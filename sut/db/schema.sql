-- MatriculaRef v1.0.0 · Esquema de la base de datos
-- Nota: la base NO impone el límite de cupo con una restricción. Esa regla (RN-CUP-01)
-- la aplica la API, que es justamente lo que se prueba.

CREATE TABLE cursos (
    codigo     VARCHAR(10) PRIMARY KEY,
    nombre     TEXT        NOT NULL,
    creditos   SMALLINT    NOT NULL CHECK (creditos BETWEEN 1 AND 6)
);

CREATE TABLE prerrequisitos (
    curso      VARCHAR(10) NOT NULL REFERENCES cursos (codigo),
    requisito  VARCHAR(10) NOT NULL REFERENCES cursos (codigo),
    PRIMARY KEY (curso, requisito)
);

CREATE TABLE estudiantes (
    id                 INT         PRIMARY KEY,
    carne              VARCHAR(12) NOT NULL UNIQUE,
    nombre             TEXT        NOT NULL,
    bloqueo_academico  BOOLEAN     NOT NULL DEFAULT FALSE,
    max_creditos       SMALLINT    NOT NULL DEFAULT 18
);

CREATE TABLE historial (
    estudiante_id  INT         NOT NULL REFERENCES estudiantes (id),
    curso          VARCHAR(10) NOT NULL REFERENCES cursos (codigo),
    estado         VARCHAR(10) NOT NULL CHECK (estado IN ('aprobado', 'reprobado', 'en_curso')),
    PRIMARY KEY (estudiante_id, curso)
);

CREATE TABLE secciones (
    id       INT         PRIMARY KEY,
    curso    VARCHAR(10) NOT NULL REFERENCES cursos (codigo),
    numero   SMALLINT    NOT NULL,
    cupo     SMALLINT    NOT NULL CHECK (cupo >= 0),
    abierta  BOOLEAN     NOT NULL DEFAULT TRUE,
    UNIQUE (curso, numero)
);

-- dia: 1 = lunes ... 6 = sábado
CREATE TABLE horarios (
    seccion_id  INT      NOT NULL REFERENCES secciones (id) ON DELETE CASCADE,
    dia         SMALLINT NOT NULL CHECK (dia BETWEEN 1 AND 6),
    inicio      TIME     NOT NULL,
    fin         TIME     NOT NULL,
    CHECK (fin > inicio)
);

CREATE TABLE inscripciones (
    id             SERIAL      PRIMARY KEY,
    estudiante_id  INT         NOT NULL REFERENCES estudiantes (id),
    seccion_id     INT         NOT NULL REFERENCES secciones (id),
    estado         VARCHAR(10) NOT NULL CHECK (estado IN ('apartada', 'confirmada', 'retirada')),
    creada         TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizada    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_inscripcion_activa
    ON inscripciones (estudiante_id, seccion_id) WHERE estado <> 'retirada';
CREATE INDEX ix_inscripciones_seccion ON inscripciones (seccion_id) WHERE estado <> 'retirada';

-- Datos del servicio de Tesorería simulado
CREATE TABLE tesoreria_bloqueos (
    estudiante_id  INT     PRIMARY KEY REFERENCES estudiantes (id),
    bloqueado      BOOLEAN NOT NULL,
    motivo         TEXT
);

-- Ocupación de cada sección (apartadas + confirmadas)
CREATE VIEW v_ocupacion AS
SELECT s.id AS seccion_id, s.curso, s.numero, s.cupo,
       COUNT(i.id) FILTER (WHERE i.estado IN ('apartada', 'confirmada')) AS inscritos
FROM secciones s
LEFT JOIN inscripciones i ON i.seccion_id = s.id
GROUP BY s.id, s.curso, s.numero, s.cupo;
