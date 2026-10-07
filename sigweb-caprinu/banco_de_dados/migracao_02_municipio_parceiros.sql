-- Migração 02 — município nas comunidades e tabelas de parceiros
--
-- Só é necessária em bancos que JÁ EXISTEM. Em banco novo, criacao_tabelas.sql
-- já vem no formato final. Não precisa aplicar à mão: o serviço sigweb-migrate
-- roda a cada `docker compose up` (ver aplicar_migracoes.sh).
--
-- É idempotente: se as tabelas de parceiros já existirem (como no servidor da
-- Caprinu, onde foram criadas à mão), o CREATE TABLE IF NOT EXISTS não mexe nelas.

BEGIN;

ALTER TABLE comunidades ADD COLUMN IF NOT EXISTS municipio VARCHAR(100);

CREATE TABLE IF NOT EXISTS parceiros (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL UNIQUE,
    sigla VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS locais_parceiros (
    id SERIAL PRIMARY KEY,
    parceiro_id INT NOT NULL REFERENCES parceiros(id) ON DELETE CASCADE,
    nome VARCHAR(150) NOT NULL,
    endereco VARCHAR(255),
    latitude  DOUBLE PRECISION NOT NULL CHECK (latitude  BETWEEN  -90 AND  90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    geom GEOMETRY(Point, 4326) GENERATED ALWAYS AS (
        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    ) STORED
);

CREATE TABLE IF NOT EXISTS acoes_parceiros (
    id SERIAL PRIMARY KEY,
    coleta_id   INT NOT NULL REFERENCES coletas_producao(id) ON DELETE CASCADE,
    parceiro_id INT NOT NULL REFERENCES parceiros(id) ON DELETE RESTRICT,
    data_acao DATE NOT NULL DEFAULT CURRENT_DATE,
    descricao TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_locais_parceiros_geom ON locais_parceiros USING gist(geom);
CREATE INDEX IF NOT EXISTS idx_locais_parceiros_parceiro ON locais_parceiros (parceiro_id);
CREATE INDEX IF NOT EXISTS idx_acoes_parceiros_coleta ON acoes_parceiros (coleta_id);
CREATE INDEX IF NOT EXISTS idx_acoes_parceiros_parceiro ON acoes_parceiros (parceiro_id);

-- A view ganha a coluna municipio. CREATE OR REPLACE VIEW só aceita colunas novas
-- no fim da lista, e aqui ela entra no meio — por isso DROP + CREATE.
DROP VIEW IF EXISTS vw_comunidades_dashboard;
CREATE VIEW vw_comunidades_dashboard AS
SELECT DISTINCT ON (c.id)
    c.id, c.nome, c.municipio, c.informacoes_adicionais, c.latitude, c.longitude,
    p.data_coleta, p.total_produtores,
    p.qtd_caprinos, p.qtd_ovinos, p.criacao_extensiva, p.criacao_semi_extensiva,
    p.criacao_intensiva, p.escrituracao_sim, p.escrituracao_nao, p.observacoes, c.geom
FROM comunidades c
LEFT JOIN coletas_producao p ON c.id = p.comunidade_id
ORDER BY c.id, p.data_coleta DESC NULLS LAST, p.id DESC;

COMMIT;
