# 6. Manutenção e continuidade

Rotinas, como alterar o sistema sem quebrá-lo, pendências conhecidas e a lista de passagem de bastão.

## Rotinas

| Rotina | Frequência sugerida | Como |
|---|---|---|
| Cadastro e atualização de dados | A cada levantamento | Painel Django (`/admin/`); depois conferir no mapa com `Ctrl+Shift+R` |
| Controle de qualidade dos dados | A cada rodada de cadastro | Consultas e conferências de [04](04-metodologia.md) |
| Backup do banco | **[preencher]** (sugestão: semanal e antes de qualquer migração) | Comandos de [05](05-reproducao.md) |
| Atualizar senhas e acessos | Quando alguém sair da equipe | `.env` e painel Django |
| Rever bibliotecas do frontend | Ocasional | Ver "Atualizar bibliotecas" |

## Como alterar o sistema

### Mudar o esquema do banco

1. Escreva `banco_de_dados/migracao_NN_descricao.sql`, com `IF NOT EXISTS` para poder rodar mais de uma vez. `NN` é o próximo número da sequência.
2. Atualize `banco_de_dados/criacao_tabelas.sql` com a mesma mudança (ele é o esquema para banco novo).
3. Ajuste `admin/sigweb/models.py` e `admin.py`. Os modelos continuam `managed = False`: o Django não cria a coluna, só passa a conhecê-la.
4. Se a view `vw_comunidades_dashboard` precisa da coluna, altere-a no SQL (`CREATE OR REPLACE VIEW`).
5. Se o mapa precisa do dado, inclua a propriedade no GeoJSON de `backend/main.py` (ver exemplo abaixo).
6. `docker compose up -d --build`: o serviço `sigweb-migrate` aplica as migrações que faltam.
7. Teste local e registre a mudança em [04](04-metodologia.md) se alterar critério.

### Exemplo: levar um campo da view até o mapa (como foi feito com `municipio`)

O `municipio` já é enviado desde 07/10/2026. O mesmo caminho serve para qualquer campo novo: ele precisa estar na view e, em `backend/main.py`, na consulta de `obter_geojson`, numa linha do `jsonb_build_object` de `properties`:

```sql
'properties', jsonb_build_object(
    'nome', nome,
    'municipio', municipio,          -- nova linha
    'informacoes_adicionais', informacoes_adicionais,
    ...
```

Depois reconstrua a API (`docker compose up -d --build`). No caso do município, o filtro aparece sozinho quando há valores; padronize a grafia no cadastro.

### Adicionar uma métrica ao seletor do mapa

1. Inclua a `<option>` no `frontend/index.html`.
2. Inclua a cor em `CORES_FILTRO` no `app.js`.
3. Inclua o rótulo e o título em `METRICAS` no `app.js`.
4. Se a métrica vem de um campo novo, siga "Mudar o esquema do banco".

### Atualizar bibliotecas

As bibliotecas do frontend vêm por CDN em **versões fixas** (lista em [`sigweb.md`](sigweb.md), seção 1). Para atualizar uma: troque a versão no `index.html`, teste o recurso que a usa (desenho e medição, calor, tela cheia, busca, clusters) e registre a nova versão. Se o sistema precisar funcionar sem depender de CDN, hospede Leaflet, Lucide e a fonte localmente.

### Depois de colar arquivos novos do frontend

Recarregue com `Ctrl+Shift+R`: o navegador guarda CSS e JS em cache. Se o HTML dinâmico ganhar ícones novos, chame `renderizarIcones()` depois de inserir o HTML. Todo texto vindo da API ou de arquivo importado que entrar em HTML novo deve passar por `esc()`.

## Pendências conhecidas

Ordenadas por prioridade. Marque aqui quando resolver.

### Antes de publicar na internet

- [x] **`POST /api/comunidades` sem autenticação:** rota removida do `backend/main.py` em 07/10/2026 (o painel grava direto no banco). Se um dia houver escrita pela API, ela precisa nascer com autenticação.
- [ ] **CORS `allow_origins=["*"]`**: restringir ao domínio do site, ou remover quando site e API estiverem no mesmo domínio.
- [ ] **Senha do banco:** o `backend/main.py` não tem mais senha padrão (07/10/2026). Falta definir uma senha forte no `.env` e conferir se `docker-compose.yml`, `.env.example` e `deploy/sigweb-api.service` ainda trazem `inovi` (`git grep -n inovi`).
- [x] **Erros do banco devolvidos ao cliente:** corrigido em 07/10/2026. A API responde mensagem genérica e grava o detalhe no log (`docker compose logs api`).
- [ ] **Licença:** escolher e criar `LICENSE`.
- [ ] **Credenciais soltas:** `git grep -n -i "senha\|password\|secret"`.
- [ ] **Dados de exemplo** (`carga_inicial.sql`): confirmar que são só de exemplo.

### Funcionalidade

- [x] **`municipio` no GeoJSON:** incluído em 07/10/2026. Falta conferir no navegador se o filtro aparece com comunidades que tenham município preenchido.
- [ ] **Parceiros não aparecem no mapa:** `parceiros`, `locais_parceiros` e `acoes_parceiros` são cadastrados no painel, mas a API não os expõe e a view não os inclui. Decidir como exibir (pinos dos locais, ações no relatório da comunidade) e criar os endpoints.
- [ ] **Unidade de `criacao_*` e `escrituracao_*`:** confirmar (produtores ou cabeças) e registrar no dicionário de [02](02-banco-de-dados.md).
- [ ] **Teste do mapa no navegador e no celular:** a lista de conferência está em [`sigweb.md`](sigweb.md), seção 8.

### Limpeza técnica

- [ ] Remover o `<script>` do `leaflet-hash` no `index.html` (o `app.js` não usa o plugin).
- [ ] Renomear `limitesNordeste` para `limitesBrasil` no `app.js`.
- [ ] Renomear `.card-texto.verde` (hoje é o destaque azul).
- [ ] Remover o bloco "Compatibilidade" do nginx quando o endereço antigo `/mapas` sair de uso.

## Passagem de bastão

Preencha antes de passar o sistema a outra pessoa ou equipe.

| Item | Registro |
|---|---|
| Repositório (endereço e quem administra) | **[preencher]** |
| Onde o sistema roda (servidor, domínio, painel de hospedagem) | **[preencher]** |
| Quem tem acesso ao servidor | **[preencher]** |
| Onde ficam as senhas (`.env`, gerenciador de senhas) | **[preencher]** (nunca no repositório) |
| Quem cria usuários no painel Django | **[preencher]** |
| Onde ficam os backups e quem os confere | **[preencher]** |
| Contato de quem conhece o sistema | **[preencher]** |
| Certificado HTTPS (renovação) | **[preencher]** |
| Fonte e responsável pelos dados de campo | **[preencher]**, ver [04](04-metodologia.md) |

Roteiro de verificação para quem assume:

1. Clonar o repositório e subir o sistema local seguindo [05](05-reproducao.md).
2. Cadastrar uma comunidade de teste e vê-la no mapa.
3. Rodar as consultas de qualidade de [02](02-banco-de-dados.md).
4. Fazer um backup e restaurá-lo em ambiente de teste.
5. Ler as pendências acima e definir prioridades.
