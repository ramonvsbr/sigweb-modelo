# Documentação técnica do SIGWeb Caprinu

Registro do desenvolvimento do SIGWeb: como o sistema é montado, como os dados são modelados e tratados, e como reconstruí-lo do zero. O objetivo é **reprodutibilidade** (outra pessoa refaz o sistema só com este repositório) e **continuidade** (quem assumir sabe o que existe, o que falta e por quê).

## Leia nesta ordem

| # | Documento | Responde a |
|---|---|---|
| 1 | [Arquitetura](01-arquitetura.md) | Quais são as peças, como se comunicam, quais são os endpoints e as decisões de projeto |
| 2 | [Banco de dados](02-banco-de-dados.md) | Quais tabelas existem, o que cada coluna guarda, como a view alimenta o mapa |
| 3 | [Geoprocessamento](03-geoprocessamento.md) | Sistema de coordenadas, geração do ponto, medições, seleção por área, mapa de calor |
| 4 | [Registro metodológico](04-metodologia.md) | De onde vêm os dados, quais critérios e regras de cálculo, limitações |
| 5 | [Reprodução](05-reproducao.md) | Passo a passo para subir o sistema do zero, local e em servidor |
| 6 | [Manutenção e continuidade](06-manutencao.md) | Rotinas, como alterar o sistema, pendências conhecidas, lista de passagem de bastão |

## Outros documentos do repositório

- [`README.md`](README.md) da raiz: visão rápida e comandos de subida.
- [`sigweb.md`](sigweb.md): descrição detalhada do **comportamento do mapa** (frontend), configurações do `app.js`, identidade visual e lista de conferência.

## Como esta documentação foi escrita

Os documentos 1 a 3 foram escritos a partir do código: `banco_de_dados/criacao_tabelas.sql`, `backend/main.py` e `admin/sigweb/models.py`. Quando algo não pôde ser confirmado no código, aparece marcado:

- **[confirmar]**: dedução razoável que alguém da equipe precisa validar.
- **[preencher]**: informação que só a equipe da Caprinu tem (origem dos dados, responsáveis, datas).

Procure por esses dois marcadores antes de considerar a documentação fechada: `git grep -n "\[preencher\]\|\[confirmar\]" -- "*.md"`.

## Mapa do código

Os caminhos desta tabela e de toda a documentação (`backend/`, `banco_de_dados/`, `frontend/`...) são relativos à pasta `sigweb-caprinu/`, onde está o projeto.

| Pasta | Documentado em |
|---|---|
| `banco_de_dados/` | [02](02-banco-de-dados.md), [03](03-geoprocessamento.md) |
| `backend/` | [01](01-arquitetura.md) |
| `admin/` | [01](01-arquitetura.md), [02](02-banco-de-dados.md) |
| `frontend/` | [03](03-geoprocessamento.md), [`sigweb.md`](sigweb.md) |
| `deploy/`, `docker-compose.yml`, `.env.example` | [05](05-reproducao.md) |