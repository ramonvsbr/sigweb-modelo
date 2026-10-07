# 4. Registro metodológico

Registra **de onde vêm os dados, que critérios o sistema aplica e onde ele pode induzir a erro**. É a parte que permite a outra equipe repetir o procedimento e interpretar os números com cuidado.

> Campos marcados com **[preencher]** só a equipe da Caprinu sabe. Complete-os antes de fechar a documentação.

## 1. Objetivo e escopo

Mapa web da caprinovinocultura no semiárido: comunidades cadastradas, rebanho (caprinos e ovinos), número de produtores, sistemas de criação, escrituração zootécnica e parceiros, com filtros, mapa de calor, medição e exportação.

- **Área de estudo:** região de Petrolina (PE) e Juazeiro (BA) e entorno **[confirmar a abrangência real dos cadastros]**.
- **Unidade de análise:** a **comunidade ou associação**, representada por **um ponto**.
- **Período dos dados:** **[preencher]**.

## 2. Origem e coleta dos dados

| Item | Registro |
|---|---|
| Quem coleta | **[preencher]** (técnicos da Caprinu?) |
| Como coleta | **[preencher]** (visita, questionário, planilha, entrevista com a liderança?) |
| Instrumento e versão | **[preencher]** |
| Como obtém a coordenada | **[preencher]** (aparelho de GPS, celular, mapa; precisão esperada) |
| Quem digita no painel | **[preencher]** |
| Frequência de atualização | **[preencher]** |
| Dados autodeclarados ou conferidos em campo? | **[preencher]** |

Cada levantamento vira uma **coleta** com data. O histórico não é sobrescrito: uma coleta nova é uma nova linha.

## 3. Regras de cálculo e critérios

| Regra | Definição | Onde está implementada |
|---|---|---|
| Dado exibido por comunidade | A coleta de **maior data** (empate: maior `id`) | View `vw_comunidades_dashboard` |
| Comunidade sem coleta | Aparece no mapa com valores **zerados** | LEFT JOIN da view; frontend trata `null` como `0` |
| Comunidade sem coordenada | **Não** aparece no mapa | `WHERE geom IS NOT NULL` na API |
| Totais da visão geral | Soma, no navegador, das comunidades **visíveis** (com os filtros aplicados) | `mostrarResumoGeral()` |
| Sistema de criação predominante | O de **maior valor** na comunidade. Empate: a comunidade conta nos dois filtros. Sem dado de sistema: some quando o filtro está ligado | Filtros no `app.js` |
| "Sem escrituração" | `escrituracao_sim = 0` (inclui comunidade sem dado) | Filtros no `app.js` |
| "Com escrituração" | `escrituracao_sim ≥ 1` | Filtros no `app.js` |
| Combinação de filtros | **E** lógico: a comunidade precisa passar em todos | Filtros no `app.js` |
| Seleção por área | Conta comunidades cujo **ponto** está dentro da forma e que passam nos filtros | Ver [03](03-geoprocessamento.md) |
| Tamanho do círculo | Função `calcularRaio()`, entre 6 e 25 px | `app.js` |
| Peso do calor | Raiz quadrada da métrica | Ver [03](03-geoprocessamento.md) |

## 4. Decisões metodológicas e justificativas

| Data | Decisão | Justificativa |
|---|---|---|
| 07/10/2026 (registro) | "Sistema" = **predominante** | Com três sistemas, "tem pelo menos um produtor" colocaria quase todas as comunidades em todos os filtros; o predominante separa melhor |
| 07/10/2026 (registro) | "Sem escrituração" = ninguém registra | Leitura mais direta de "onde estão as comunidades sem escrituração?" |
| 07/10/2026 (registro) | Filtros e métrica independentes | A métrica muda **como** desenhar; os filtros mudam **quais** comunidades |
| 07/10/2026 (registro) | Raiz quadrada no peso do calor | Evita que uma comunidade muito grande apague as demais |
| 07/10/2026 (registro) | Legenda com tamanhos reais (`calcularRaio`) | A legenda nunca diverge do mapa |
| 07/10/2026 (registro) | Seleção por área usa os filtros | O número do painel bate com o que está desenhado |
| 07/10/2026 (registro) | Círculo exportado como polígono de 64 lados | GeoJSON não tem círculo |
| 07/10/2026 (registro) | `VISTA_INICIAL` por estimativa | Não é um limite oficial; ajuste conforme os cadastros |

As datas acima são a do **registro** da decisão neste documento. Se a decisão foi tomada antes, ajuste para a data real **[preencher]**.

## 5. Limitações e cuidados de interpretação

1. **O mapa mostra a última coleta**, não a série histórica. Para evolução no tempo, consulte `coletas_producao` direto ([02](02-banco-de-dados.md)).
2. **Zero pode significar "sem dado".** Comunidade sem coleta e comunidade com valor 0 aparecem iguais. Verifique antes de concluir que não há produção.
3. **"Sem escrituração" inclui "sem dado".** Pelo critério adotado, quem não tem coleta cai nesse grupo.
4. **Soma dos sistemas e total de produtores não são validados pelo banco.** Podem não fechar.
5. **O calor não é densidade real.** Cada comunidade é um ponto ponderado pela métrica; o desfoque é visual.
6. **Medidas desenhadas são esféricas** e valem para a forma na tela ([03](03-geoprocessamento.md)).
7. **Coordenada digitada à mão pode estar errada** (por exemplo, latitude e longitude trocadas). A consulta de verificação de [02](02-banco-de-dados.md) pega os casos grosseiros, não os pequenos.
8. **Dados de `carga_inicial.sql` são de exemplo**; não use esses números em análises.
9. **Parceiros:** o cadastro existe no painel, mas o mapa ainda não os exibe ([06](06-manutencao.md)).
10. **A "visão geral" depende dos filtros:** com filtro ativo, os totais valem só para o conjunto filtrado.

## 6. Controle de qualidade

Procedimento sugerido a cada rodada de cadastro **[confirmar com a equipe]**:

1. Rodar a consulta de **coordenadas fora da área** e corrigir.
2. Rodar a consulta de **comunidades sem coleta** e decidir se faltam dados ou se a comunidade deve sair.
3. Conferir se os **sistemas de criação** somam o esperado e se `escrituracao_sim + escrituracao_nao` bate com o total de produtores (se essa for a regra adotada).
4. Padronizar o **nome do município** (mesma grafia sempre; o filtro lista os valores existentes).
5. Comparar os **totais do mapa** com a consulta de totais do banco.
6. Abrir 2 ou 3 comunidades no mapa e conferir contra a planilha ou o formulário de campo.

## 7. Versionamento e rastreabilidade

- **Dados:** coletas com data; cada alteração relevante vira nova coleta.
- **Código e documentação:** Git. Cada mudança de método (critério de filtro, fórmula, regra de seleção) deve ir num commit com mensagem clara **e** uma linha na tabela abaixo.
- **Versões das bibliotecas:** fixas por CDN, listadas em [`sigweb.md`](sigweb.md), seção 1.

## 8. Registro de alterações do método

| Data | Mudança | Motivo | Responsável |
|---|---|---|---|
| | | | |
