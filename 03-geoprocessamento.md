# 3. Geoprocessamento

Descreve cada operação espacial do sistema, onde ela acontece (banco ou navegador) e como conferi-la. Os números exatos de configuração estão no `frontend/app.js` (constantes citadas abaixo) e em [`sigweb.md`](sigweb.md).

## 1. Sistema de referência

| Item | Valor |
|---|---|
| Sistema de coordenadas | **EPSG:4326** (WGS 84), graus decimais, o mesmo do GPS e dos mapas da internet |
| Ordem no banco e no GeoJSON | **longitude, latitude** (`ST_MakePoint(longitude, latitude)`; `coordinates: [lon, lat]`) |
| Ordem no Leaflet (quando manual) | **latitude, longitude**; o Leaflet inverte sozinho ao ler GeoJSON |
| Entrada de dados | Latitude e longitude **separadas**, em graus decimais, negativas ao sul e a oeste (Ex.: `-9.3845`, `-40.2534`) |

Erro clássico a evitar: trocar latitude e longitude no cadastro. Na região de Petrolina (PE) e Juazeiro (BA) a latitude é próxima de `-9` e a longitude próxima de `-40`. Valores trocados jogam o ponto no oceano ou fora do Brasil (a consulta de verificação está em [02](02-banco-de-dados.md)).

## 2. No banco (PostGIS)

### Geração do ponto

A coluna `geom` é **gerada** e armazenada:

```sql
geom GEOMETRY(Point, 4326) GENERATED ALWAYS AS (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
) STORED
```

Efeito: não há como o ponto do mapa divergir dos números cadastrados; quem edita a latitude ou a longitude atualiza o ponto automaticamente.

### Serialização para o mapa

A API converte a geometria para GeoJSON dentro do próprio banco:

```sql
'geometry', ST_AsGeoJSON(geom)::jsonb
```

O resultado é uma `FeatureCollection` de pontos, que o Leaflet consome direto. Registros com `geom IS NULL` são excluídos, porque o Leaflet quebra com geometria nula.

### Índice espacial

`idx_comunidades_geom` (GiST) organiza os pontos por quadrantes, em vez de ler linha por linha. Hoje a API lê todos os pontos; o índice serve a consultas por área que venham a ser feitas no banco.

## 3. No navegador (Leaflet e Turf.js)

Todas as medições e seleções abaixo são calculadas no navegador. Nada é gravado no banco.

| Operação | Como é calculada | Saída |
|---|---|---|
| Distância (linha) | Turf.js, comprimento da linha | km e m |
| Área (polígono, retângulo) | Turf.js, `area` em m² | hectares (`m² ÷ 10.000`) e m² |
| Perímetro (polígono, retângulo) | Turf.js, comprimento do contorno | km |
| Círculo | Raio em **metros reais** (Geoman `drawCircle`); área calculada a partir do raio | raio em km e m; área em ha e m² |
| Comunidades dentro de polígono ou retângulo | `turf.booleanPointInPolygon` sobre o ponto de cada comunidade | contagem e totais |
| Comunidades dentro de círculo | Distância do centro até a comunidade (`distanceTo` do Leaflet, em metros) comparada ao raio | contagem e totais |
| Exportar círculo | `turf.circle` com 64 lados | polígono (GeoJSON não tem círculo); o raio vai nas propriedades |

Detalhes de uso:

- **Quais comunidades entram na seleção:** só as que passam nos filtros ativos, as mesmas desenhadas no mapa. Assim o número do painel bate com o que se vê.
- **Linhas não selecionam nada.**
- **Ponto na borda:** vale o ponto da comunidade; um ponto exatamente sobre a borda pode entrar ou não, conforme o arredondamento. Se um caso de borda importar, confira à mão.
- **Medições vs. versão paga do Geoman:** o Geoman gratuito não mede sozinho; por isso o Turf.js faz as contas.
- **Número formatado em português** (vírgula decimal) apenas na exibição; os valores exportados em GeoJSON usam número comum.

### Mapa de calor

| Item | Valor |
|---|---|
| Biblioteca | `leaflet.heat` |
| Peso de cada comunidade | **raiz quadrada** da métrica atual (ovinos, caprinos ou produtores) |
| Motivo da raiz | Com poucas comunidades muito maiores que as outras, o peso linear apagaria o resto |
| Gradiente | azul, azul da marca, âmbar, vermelho (`GRADIENTE_CALOR`) |

O calor mostra a **distribuição ponderada dos pontos cadastrados**, não uma densidade real de animais por área: cada comunidade é um ponto, e o desfoque é visual.

### Tamanho e cor dos círculos

O raio vem de `calcularRaio()`, limitado entre **6 e 25 px**. A legenda usa a mesma função, então nunca diverge do mapa. A cor depende da métrica (`CORES_FILTRO`).

### Área navegável e vista inicial

| Constante | Valor | Observação |
|---|---|---|
| `LIMITES` | sul -35, norte 6, oeste -75, leste -28 | Brasil com cerca de 1° de margem; o usuário não arrasta para fora |
| `VISTA_INICIAL` | de (-9,70; -40,90) a (-9,10; -40,10) | Região de Petrolina e Juazeiro. **É uma estimativa**, não um limite oficial |

### Camadas GeoJSON importadas

O usuário pode importar arquivos GeoJSON (por exemplo, limites municipais). Regras de validação:

- Só pontos, linhas e polígonos em WGS 84 (latitude e longitude).
- Recusa: JSON inválido, arquivo sem geometria, `crs` declarado diferente de EPSG:4326/CRS84, e coordenadas fora da área navegável (sinal de arquivo em outro sistema, como UTM).
- Limite de **20 MB** por arquivo (`TAMANHO_MAX_GEOJSON`).
- As camadas existem só na sessão e não são enviadas à API.

## 4. Precisão e limitações

- **Cálculos esféricos:** as medições do Turf.js usam aproximação esférica da Terra, não o elipsoide. Em polígonos pequenos (comunidades, propriedades) a diferença é pequena; para laudos oficiais, valide no QGIS (abaixo).
- **Resolução da coordenada:** a exibição usa 5 casas decimais, cerca de 1,1 m na linha do equador. A precisão real depende do aparelho de GPS usado em campo **[preencher]** (aparelho e método de coleta).
- **Medidas ao desenhar** valem para a forma como está na tela: o mapa em tela não substitui levantamento topográfico.
- **Desenhos não são salvos:** somem ao recarregar; para guardá-los, exporte o GeoJSON.

## 5. Como validar os resultados

1. Desenhe uma forma no mapa e baixe o GeoJSON dos desenhos (botão de download abaixo da barra de desenho).
2. Abra o arquivo no QGIS ou em geojson.io e confira a posição da forma.
3. No QGIS, calcule a área com elipsoide (`$area`, com o elipsoide do projeto em WGS 84) e compare com `area_ha` das propriedades. Espere diferença pequena.
4. Para a seleção por área, some à mão os valores das comunidades que visualmente estão dentro e compare com o painel. Teste também uma comunidade bem na borda.
5. Para os totais da visão geral, compare com a consulta de totais de [02](02-banco-de-dados.md).
