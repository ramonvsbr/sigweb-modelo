# 5. Reprodução: subir o SIGWeb do zero

Passo a passo para reconstruir o sistema só com este repositório, em ambiente local e em servidor.

## Pré-requisitos

| Item | Para quê |
|---|---|
| Git | Clonar o repositório |
| Docker Desktop (ou Docker Engine + Compose) | Banco, migrações, API e painel. **Precisa estar aberto/rodando** |
| Python 3 | Só para servir o frontend com `python -m http.server` (qualquer servidor estático serve) |
| Navegador atual | Ver o mapa |

## Local, com Docker

### 1. Obter o código

```bash
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
cd SEU_REPOSITORIO
```

(Se o repositório tiver a pasta `sigweb-caprinu/` dentro, entre nela.)

### 2. Configurar o `.env`

```bash
cp .env.example .env        # PowerShell: copy .env.example .env
```

| Variável | O que fazer |
|---|---|
| `DB_PASSWORD` | Defina uma senha. **Obrigatória:** a API não sobe sem ela (no uso local, qualquer uma) |
| `DJANGO_SECRET_KEY` | Texto longo e aleatório |
| `DJANGO_SUPERUSER_*` | Usuário, e-mail e senha do primeiro administrador do painel |
| `API_PORT` | Porta da API (padrão 8000) |
| `ADMIN_PORT` | Porta do painel (padrão 8002) |
| `DJANGO_USAR_HTTPS` | **`False`** em `http://localhost`; senão o login do painel não funciona |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | Só em servidor com domínio (ver abaixo) |

O `.env` **nunca** vai para o Git (já está no `.gitignore`).

### 3. Subir os serviços

```bash
docker compose up -d --build
docker compose ps
```

O primeiro `up` demora (download de imagens). Resultado esperado:

| Serviço | Endereço | Estado |
|---|---|---|
| `sigweb-db` | `127.0.0.1:5433` | rodando |
| `sigweb-migrate` | n/a | roda e sai (normal) |
| `api` | `127.0.0.1:8000` | rodando |
| `admin` | `127.0.0.1:8002` | rodando |

### 4. Verificar a API

Abra no navegador `http://127.0.0.1:8000/api/comunidades/geojson`. Deve aparecer um GeoJSON começando com `{"type":"FeatureCollection"`. No terminal use `curl http://127.0.0.1:8000/api/comunidades/geojson` (no PowerShell, `curl.exe`, porque `curl` é apelido de `Invoke-WebRequest` e pede confirmação).

### 5. Servir o mapa

```bash
cd frontend
python -m http.server 5500       # Windows: py -m http.server 5500
```

Abra **`http://localhost:5500`**. Use `localhost` ou `127.0.0.1`, **não** o IP da rede: nesses dois endereços o `app.js` busca a API em `http://127.0.0.1:8000`; em qualquer outro ele busca `/api/...` no próprio servidor estático e mostra "API indisponível".

### 6. Cadastrar dados

1. Abra `http://localhost:8002/` e entre com o usuário definido no `.env`.
2. Os dados de `carga_inicial.sql` são de exemplo: apague e cadastre os reais.
3. Cadastre a comunidade (nome, município, latitude, longitude) e uma coleta.
4. Volte ao mapa e recarregue com `Ctrl+Shift+R`.

### Parar e retomar

```bash
docker compose stop        # pausa, mantém os dados
docker compose up -d       # volta
docker compose down -v     # apaga tudo, inclusive o banco
```

## Em servidor (site próprio)

Pensado para um domínio dedicado, por exemplo `sigweb.exemplo.org`.

| Endereço | O que serve |
|---|---|
| `/` | frontend estático (`frontend/`) |
| `/api/` | API (porta `API_PORT`) |
| `/admin/` | painel de cadastro (porta `ADMIN_PORT`) |
| `/static/` | CSS e JS do painel Django |

1. Copie o repositório para `/var/www/sigweb-caprinu/` e suba os containers como acima.
2. Instale `deploy/nginx-sigweb.conf` (passo a passo e HTTPS com certbot no início do arquivo).
3. No `.env`: `DJANGO_ALLOWED_HOSTS=sigweb.exemplo.org`, `DJANGO_CSRF_TRUSTED_ORIGINS=https://sigweb.exemplo.org` e `DJANGO_USAR_HTTPS=True`.
4. Antes de abrir ao público, resolva as pendências de segurança de [01](01-arquitetura.md) e [06](06-manutencao.md).

O nginx mantém também `/mapas/api/` (repassado a `/api/`) por compatibilidade com o `app.js` antigo; apague esse bloco quando a migração terminar.

A API pode rodar sem Docker pelo `deploy/sigweb-api.service`, **nunca junto** com o serviço `api` do compose.

## Backup e restauração do banco

Ajuste o nome do serviço, usuário e banco conforme o seu `docker-compose.yml` e `.env` **[confirmar]**. O padrão do código é banco `sigweb_caprinu`, usuário `postgres`.

```bash
# backup
docker compose exec sigweb-db pg_dump -U postgres sigweb_caprinu > backup_AAAA-MM-DD.sql

# restauração (em banco vazio)
docker compose exec -T sigweb-db psql -U postgres sigweb_caprinu < backup_AAAA-MM-DD.sql
```

Guarde os backups **fora** do repositório e do servidor.

## Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `docker compose` dá erro de conexão | Docker Desktop fechado | Abrir o Docker Desktop |
| Porta em uso (5433, 8000, 8002, 5500) | Outro programa usa a porta | Mudar `API_PORT` ou `ADMIN_PORT` no `.env`, ou outra porta no `http.server` |
| Mapa com "API indisponível" | API fora do ar, ou acesso pelo IP da rede | Testar o passo 4; abrir por `localhost`; `docker compose logs api` |
| API não sobe e o log diz que `DB_PASSWORD` não está definida | Variável ausente no `.env` ou não repassada ao container | Preencher `DB_PASSWORD` no `.env`; `docker compose up -d --build`; `docker compose logs api` |
| Login do painel não entra | `DJANGO_USAR_HTTPS=True` em `http` | Ajustar para `False` |
| Painel sem CSS | Arquivos estáticos do Django | `docker compose logs admin` |
| Cadastrei e não aparece no mapa | Cache do navegador, ou comunidade sem coordenada | `Ctrl+Shift+R`; conferir latitude e longitude |
| Filtro de município não aparece | Nenhuma comunidade tem município preenchido, ou a API em execução é anterior à inclusão de `municipio` | Preencher o município no painel; `docker compose up -d --build` para atualizar a API; `Ctrl+Shift+R` |
| Erro de um serviço | n/a | `docker compose logs NOME` (por exemplo `api`, `admin`) |
