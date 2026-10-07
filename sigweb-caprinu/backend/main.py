from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()
log = logging.getLogger("sigweb.api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que qualquer frontend acesse a API nesta fase de desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. CONEXÃO COM O BANCO (Com a correção de UTF-8 inclusa)
# Defina as variáveis de ambiente DB_HOST, DB_NAME, DB_USER e DB_PASSWORD (no
# Docker, vêm do .env; sem Docker, ver deploy/sigweb-api.service). Host, porta,
# banco e usuário têm padrão local; a SENHA NÃO tem padrão de propósito: a API
# se recusa a subir sem ela, para nunca rodar com uma senha conhecida.
DB_PASSWORD = os.getenv("DB_PASSWORD")
if not DB_PASSWORD:
    raise RuntimeError(
        "A variável de ambiente DB_PASSWORD não está definida. "
        "Defina-a no .env (Docker) ou no ambiente do serviço."
    )

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "sigweb_caprinu"),
        user=os.getenv("DB_USER", "postgres"),
        password=DB_PASSWORD,
        client_encoding="utf8",
        cursor_factory=RealDictCursor
    )

# Rota de teste que já criamos
@app.get("/")
async def rota_teste():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT postgis_version();")
        versao = cursor.fetchone()
        cursor.close(); conn.close()
        return {"status": "Sucesso!", "postgis": versao}
    except Exception:
        # O detalhe vai para o log do servidor, não para quem chamou a rota.
        log.exception("Falha no teste de conexão com o banco")
        return {"status": "Erro", "detalhes": "Banco de dados indisponível. Veja o log da API."}

# Não há rota de escrita nesta API: ela só lê. O cadastro de comunidades e
# coletas é feito pelo painel Django (admin/), que grava direto no banco.
# (A antiga rota POST /api/comunidades foi removida: não tinha autenticação.)

# 2. ROTA GET (GeoJSON): Transforma os dados do banco direto no formato do mapa
@app.get("/api/comunidades/geojson")
async def obter_geojson():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT jsonb_build_object(
                'type', 'FeatureCollection', 
                'features', jsonb_agg(feature)
            ) as geojson
            FROM (
                SELECT jsonb_build_object(
                    'type', 'Feature', 
                    'id', id, 
                    'geometry', ST_AsGeoJSON(geom)::jsonb,
                    'properties', jsonb_build_object(
                        'nome', nome, 
                        'municipio', municipio,
                        'informacoes_adicionais', informacoes_adicionais, 
                        'total_produtores', total_produtores, 
                        'qtd_caprinos', qtd_caprinos, 
                        'qtd_ovinos', qtd_ovinos, 
                        'criacao_extensiva', criacao_extensiva,
                        'criacao_semi_extensiva', criacao_semi_extensiva,
                        'criacao_intensiva', criacao_intensiva,
                        'escrituracao_sim', escrituracao_sim,
                        'escrituracao_nao', escrituracao_nao,
                        'observacoes', observacoes
                    )
                ) AS feature
                FROM vw_comunidades_dashboard
                -- Comunidade sem coordenada não vira ponto: o Leaflet quebra
                -- ao receber uma feature com geometry nula.
                WHERE geom IS NOT NULL
            ) features;
        """
        cursor.execute(query)
        res = cursor.fetchone()
        
        if res['geojson'] and res['geojson']['features'] is not None:
            return res['geojson']
        else:
            return {"type": "FeatureCollection", "features": []}
            
    except Exception:
        # O detalhe vai para o log do servidor, não para o navegador.
        log.exception("Falha ao montar o GeoJSON das comunidades")
        raise HTTPException(status_code=500, detail="Erro interno ao carregar as comunidades.")
    finally: 
        cursor.close(); conn.close()