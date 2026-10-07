# SIGWeb Caprinu

Mapa web da caprinovinocultura no semiárido: comunidades cadastradas, rebanho,
sistemas de criação, escrituração zootécnica e parceiros, com filtros, mapa de calor,
medição e exportação.

## Documentação

| Para quem | Onde ler |
|---|---|
| Quem vai **manter ou reproduzir** o sistema | [Documentação técnica](DOCUMENTACAO.md): arquitetura, banco de dados, geoprocessamento, metodologia, reprodução e manutenção |
| Quem vai **usar** o mapa (produtores, técnicos, pesquisadores) | Manual do usuário (em elaboração) |
| Quem quer o **detalhe do mapa** (filtros, medição, exportação, configurações) | [`sigweb.md`](sigweb.md) |

```
sigweb-modelo/                 raiz do repositório
├── README.md                  esta página
├── DOCUMENTACAO.md            índice da documentação técnica (01-arquitetura.md a 06-manutencao.md)
├── sigweb.md                  detalhe do mapa: comportamento, configurações e conferência
└── sigweb-caprinu/            o projeto (todos os comandos abaixo rodam aqui dentro)
    ├── frontend/              mapa (Leaflet): index.html, app.js, style.css — arquivos estáticos
    ├── backend/               API (FastAPI): entrega o GeoJSON das comunidades
    ├── admin/                 painel de cadastro (Django): comunidades, coletas e parceiros
    ├── banco_de_dados/        SQL do PostGIS: esquema, migrações e dados de exemplo
    ├── deploy/                nginx-sigweb.conf e sigweb-api.service (publicação em servidor)
    ├── docker-compose.yml     banco + migrações + API + painel
    └── .env.example           variáveis de ambiente (copie para .env)
```

Os caminhos citados na documentação (`backend/main.py`, `banco_de_dados/...`, `frontend/...`) são relativos à pasta `sigweb-caprinu/`.

## Como as partes se falam

```
Técnico ──► admin (Django) ──┐
                             ▼
                      PostgreSQL + PostGIS ──► API (FastAPI) ──► frontend (Leaflet)
```

O painel **escreve** no banco, o mapa só **lê** pela API. O SQL de `banco_de_dados/` é a
fonte da verdade do esquema; o Django nunca cria nem altera as tabelas do mapa.

## Subir tudo (Docker)

```bash
cd sigweb-caprinu
cp .env.example .env      # edite DB_PASSWORD, DJANGO_SECRET_KEY e a senha do admin
docker compose up -d --build
```

| Serviço | Endereço | O que faz |
|---|---|---|
| `sigweb-db` | `127.0.0.1:5433` | PostgreSQL + PostGIS |
| `sigweb-migrate` | — | aplica as `migracao_NN_*.sql` que faltam e sai |
| `api` | `127.0.0.1:8000` (`API_PORT`) | GeoJSON em `/api/comunidades/geojson` |
| `admin` | `127.0.0.1:8002` (`ADMIN_PORT`) | painel de cadastro |

1. Abra o painel em `http://localhost:8002/` e entre com o usuário de `DJANGO_SUPERUSER_*`.
2. Sirva o mapa: `cd frontend && python -m http.server 5500` e abra `http://localhost:5500`.
   Em `localhost`, o `app.js` busca a API em `http://127.0.0.1:8000`.

Os dados de `carga_inicial.sql` são de exemplo: apague e cadastre os reais pelo painel.

## Publicar como site próprio

Pensado para um domínio dedicado, por exemplo `sigweb.exemplo.org`:

| Endereço | O que serve |
|---|---|
| `/` | frontend estático (`frontend/`) |
| `/api/` | API (porta `API_PORT`, padrão 8000) |
| `/admin/` | painel de cadastro (porta `ADMIN_PORT`, padrão 8002) |

1. Copie a pasta `sigweb-caprinu/` (de dentro do repositório) para `/var/www/sigweb-caprinu/` e suba os containers como acima.
2. Instale `deploy/nginx-sigweb.conf` (o passo a passo, com o certificado HTTPS, está no início do arquivo).
3. No `.env`, defina `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` e `DJANGO_USAR_HTTPS=True`.

Fora de `localhost`, o `app.js` busca os dados em `/api/comunidades/geojson`, no próprio site.

### Migrando do endereço antigo (`/mapas`)

O `app.js` antigo busca os dados em `/mapas/api/...`; o novo busca em `/api/...`.
O `nginx-sigweb.conf` já atende os dois caminhos (`/mapas/api/` é repassado à API como `/api/`),
então trocar os arquivos do frontend não derruba o site. Se o `/mapas` antigo roda em
**outro** servidor, não troque o `app.js` lá antes de ele ter também um `location /api/`
para a API; ou mantenha o `app.js` antigo até apontar tudo para o domínio novo.
Quando a migração acabar, apague o bloco "Compatibilidade" do nginx.

A API também pode rodar sem Docker, pelo `deploy/sigweb-api.service`
(alternativa ao serviço `api` do compose, nunca os dois juntos).

## Mudar o esquema do banco

1. Escreva `banco_de_dados/migracao_NN_descricao.sql` (com `IF NOT EXISTS`) e atualize `criacao_tabelas.sql`.
2. Ajuste `admin/sigweb/models.py` e `admin.py`.
3. `docker compose up -d --build`.

## Antes de tornar o repositório público

- Defina uma `DB_PASSWORD` forte no `.env` (a API não sobe sem ela) e confira com `git grep -n inovi` que nenhum arquivo ainda traz a senha padrão antiga.
- Restrinja o `allow_origins=["*"]` em `backend/main.py` ao domínio do site.
- Nunca suba o `.env`. Ele já está no `.gitignore`.
- Escolha uma licença (`LICENSE`).