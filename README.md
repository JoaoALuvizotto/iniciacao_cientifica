# Módulo Parser & Pipeline Lattes

Componente central de extração, estruturação, reconciliação de entidades, análise de redes de colaboração e processamento de linguagem natural (PLN) sobre dados da Plataforma Lattes.

O pipeline transforma arquivos HTML brutos exportados do Lattes em documentos JSON altamente enriquecidos, com histórico institucional georreferenciado, produções bibliográficas estruturadas, projetos com resumos para modelagem semântica e rastreabilidade total de coautorias.

---

## Sumário

1. [Visão Geral dos Componentes](#visão-geral-dos-componentes)
2. [Funcionalidades e Melhorias Implementadas](#funcionalidades-e-melhorias-implementadas)
3. [Métricas de Validação e Qualidade dos Dados](#métricas-de-validação-e-qualidade-dos-dados)
4. [Esquema do JSON Gerado](#esquema-do-json-gerado)
5. [Instalação e Dependências](#instalação-e-dependências)
6. [Guia de Execução](#guia-de-execução)

---

## Visão Geral dos Componentes

| Arquivo / Diretório | Responsabilidade |
| :--- | :--- |
| **`parser.py`** | Parser estrutural baseado em BeautifulSoup e lxml. Processa os HTMLs de `curriculos/`, higieniza anomalias de codificação e gera os documentos JSON em `curriculos_json/`. |
| **`filling_idlattes.py`** | Algoritmo determinístico de *Entity Resolution* (resolução de entidades) para coautores e alunos presentes em artigos, anais e orientações. Emite a trilha de auditoria em `filled_idlattes_log.csv`. |
| **`queries.py`** | Algoritmos de inferência de redes de colaboração: identificação de arestas entre pesquisadores monitorados, cálculo de **ineditismo de parcerias** (novas colaborações ao longo dos anos) e mapeamento espaçotemporal do local de cada autor no ano de publicação. |
| **`pln_estudo.py`** | Pipeline não supervisionado de modelagem de tópicos e clusterização semântica: extração de keyphrases com spaCy e **KeyBERT** (usando MMR), vetorização com **SentenceTransformers** (`paraphrase-multilingual-MiniLM-L12-v2`), redução de dimensionalidade não-linear por **UMAP** e clusterização com **HDBSCAN**. |
| **`pln.py` / `teste_pln.py`** | Rotinas complementares de validação para tokenização, lematização, remoção de stopwords e anotação morfossintática (POS) via modelo `pt_core_news_sm` do spaCy. |
| **`validar_tudo.py`** | Script de auditoria automatizada que percorre toda a base JSON gerada, emitindo percentuais de conformidade, cobertura de campos e validação de casos de teste específicos. |
| **`import_mongo.py`** | Rotina de carga em lote dos documentos JSON para coleções MongoDB (com suporte a conexões locais ou instâncias de nuvem MongoDB Atlas). |
| **`curriculos/`** | Diretório de entrada contendo os arquivos HTML brutos do Lattes, indexados pelo ID Lattes de 16 dígitos. |
| **`curriculos_json/`** | Repositório de saída contendo os documentos JSON enriquecidos, indexados pelo nome completo do pesquisador. |
| **`filled_idlattes_log.csv`** | Log detalhado de auditoria de cada atribuição de ID realizada pelo `filling_idlattes.py`. |
| **`arquivo IDs lattes.txt`** | Catálogo de referência com os IDs Lattes de 16 dígitos monitorados. |

---

## Funcionalidades e Melhorias Implementadas

### 1. Extração Profunda de Projetos de Pesquisa para PLN
- **Captura de Resumos/Objetivos (`descricao`)**: Extração do texto descritivo contido na célula de cada projeto, viabilizando análises de PLN e agrupamento semântico de temas de pesquisa.
- **Metadados Estruturados**: Coleta de `situacao` ("Concluído", "Em andamento"), `natureza` ("Pesquisa", "Desenvolvimento") e lista estruturada de `integrantes` com dicionários contendo `nome` e `papel` ("Coordenador", "Integrante").
- **Divisão Cronológica**: Separação clara em `ano_inicio` (int) e `ano_fim` (int ou `"Atual"`), mantendo o campo textual `periodo` original para retrocompatibilidade.

### 2. Estruturação Rigorosa de Artigos e Anais de Congressos
- **Artigos em Periódicos (`listaPB`)**:
  - Extração rigorosa do campo `ano` prioritariamente da tag nativa `<span class="informacao-artigo" data-tipo-ordenacao="ano">` e fallback via expressão regular.
  - Coleta de link direto `doi`, lista de `colaboradores` estruturados (`nome`, `id_lattes`) e citação limpa em `texto_completo`.
- **Trabalhos em Anais de Congressos (`trabalhos_completos`)**:
  - Conversão de strings de citação ABNT brutas em objetos estruturados contendo `titulo`, `ano`, `doi`, `colaboradores`, `detalhes` (conferência, volume, páginas) e `texto_completo`.
- **Demais Produções**:
  - Estruturação equivalente para `resumos_expandidos`, `resumos_publicados` e `producao_revistas` (artigos em jornais e revistas de divulgação).

### 3. Objeto `locais_georreferenciamento` para Consultas Espaciais e Históricas
- **Unificação Espacial**: Substitui e unifica o antigo array `enderecos_historicos` em uma estrutura única, limpa e padronizada voltada a consultas espaciais, SIG e grafos temporais:
  ```json
  {
      "tipo": "atual" | "historico",
      "instituicao": "Universidade Federal de São Carlos, UFSCAR, Brasil.",
      "ano_inicio": 2011,
      "ano_fim": "Atual",
      "municipio": "Sorocaba",
      "estado": "SP",
      "pais": "Brasil"
  }
  ```
- **Resolução de `ano_inicio` das Afiliações Atuais**: As instituições ativas (`ano_fim == 'Atual'`) têm seus anos de início (`ano_inicio`) extraídos diretamente dos períodos de atuação da seção `AtuacaoProfissional`, eliminando valores nulos.
- **Catálogo Institucional Inteligente (`INSTITUICOES_GEO`)**: Mapeamento interno de mais de 70 universidades e centros de pesquisa (UFSCAR, UNICAMP, USP, UNESP, EMBRAPA, ITAL, CNPEM, etc.) com detecção de campus específico (ex.: "Campus Sorocaba") e instituições internacionais (Alemanha, Itália, Portugal, Reino Unido, EUA, Japão).

### 4. Enriquecimento de Citações Bibliográficas via Pipeline em Camadas (`listaNomesCitacao`)
- **Pipeline em 3 Camadas (`enrich_citation_names()`)**:
  1. **Camada 1 (Nativo)**: Preserva e limpa as variações cadastradas oficialmente no Lattes pelo próprio pesquisador.
  2. **Camada 2 (Empírico)**: Minera as publicações do próprio autor (`listaPB`, `trabalhos_completos`, etc.), identificando as assinaturas reais e empíricas utilizadas nos periódicos através do classificador `eh_mesmo_autor()` (sem geração sintética ou artificial de citações).
  3. **Camada 3 (Higienização)**: Deduplica variações por chave normalizada, eliminando falsos positivos e ruídos.
- **Resultado**: Resolução fidedigna das citações a partir do Lattes e produções reais, sem invenção de nomes sintéticos de citação.

### 5. Resolução Determinística de Entidades (`filling_idlattes.py`)
- **Separação de Responsabilidades**: O `parser.py` é responsável pela extração fiel do HTML; o `filling_idlattes.py` executa a reconciliação e preenchimento dos IDs Lattes faltantes com base no nome completo e na `listaNomesCitacao`.
- **Normalização Unicode NFKD**: Comparação textual resiliente a diacríticos, pontuações e maiúsculas/minúsculas.
- **Auditoria Completa**: Geração de `filled_idlattes_log.csv` classificando cada resolução em:
  - `proprio_pesquisador`: identificação do autor do currículo em sua própria publicação.
  - `coautor_reconhecido`: identificação de outro pesquisador monitorado na rede.
  - `aluno_orientacao`: identificação do orientado em orientações concluídas ou em andamento.

### 6. Higienização de Anomalias de Codificação do Lattes
- **Correção de Ruídos do CNPq**: A função `limpar_texto()` trata sistematicamente a substituição indevida de travessões (*en-dash*) e aspas pelo caractere `?` na exportação original do CNPq:
  - `"WCAMA 2014 ? V Workshop"` $\rightarrow$ `"WCAMA 2014 - V Workshop"`
  - `"?PAMDA?"` $\rightarrow$ `"PAMDA"`
- Unificação de múltiplos espaços, quebras de linha e normalização de pontuação final de citações.

### 7. Análise de Redes e Dinâmica Espaço-Temporal (`queries.py`)
- **Detecção de Colaborações**: Cruzamento de coautorias via ID Lattes e nomes de citação entre todos os membros cadastrados.
- **Ineditismo de Parcerias**: Ordenação cronológica para identificar exatamente em que ano e artigo duas pessoas colaboraram pela primeira vez.
- **Geolocalização Temporal**: Cruzamento do ano da publicação com o histórico de afiliações para determinar onde cada autor estava vinculado no momento exato do trabalho.

### 8. Modelagem Semântica e Clusterização de Tópicos (`pln_estudo.py`)
- Agregação do corpus textual recente (últimos N anos) combinando:
  - Títulos e descrições/resumos de **projetos de pesquisa**.
  - Títulos de artigos em periódicos (`listaPB`) e anais (`trabalhos_completos`).
  - Orientações concluídas e em andamento.
  - Linhas de pesquisa e áreas de atuação.
- Extração de keyphrases bi-gram e tri-gram via KeyBERT com diversidade (MMR).
- Geração de embeddings densos multilíngues, redução UMAP e agrupamento com HDBSCAN para mapeamento de áreas de especialização emergentes.

---

## Métricas de Validação e Qualidade dos Dados

Estatísticas consolidadas obtidas via `validar_tudo.py` sobre os 54 currículos analisados:

| Categoria | Total / Métrica | Taxa de Conformidade |
| :--- | :--- | :--- |
| **Projetos de Pesquisa** | 1.132 projetos catalogados | **82,7%** com descrição/resumo preenchido (936 projetos)<br>**100%** com `ano_inicio` e `ano_fim` separados |
| **Artigos em Periódicos (`listaPB`)** | 5.849 artigos | **100%** com campo `ano` estruturado<br>**42,0%** dos autores com `id_lattes` resolvido (14.525) |
| **Trabalhos em Congressos (`trabalhos_completos`)** | 3.050 trabalhos | **100%** estruturados como dicionários<br>**100%** com campo `ano` estruturado<br>**63,2%** dos autores com `id_lattes` resolvido (8.130) |
| **Produção em Revistas e Jornais** | 263 produções | **75,0%** dos autores com `id_lattes` resolvido (357 de 476) |
| **Resoluções de ID (`filled_idlattes_log.csv`)** | 15.921 IDs preenchidos | **14.096** autor próprio · **1.807** coautores · **18** orientandos |
| **Afiliações e Endereços Históricos** | 54 de 54 pesquisadores com histórico | **100%** de cobertura (417 vínculos históricos no total)<br>**58,3%** com município e UF resolvidos |
| **Locais de Georreferenciamento** | 54 pesquisadores | **417 pontos geográficos** (150 afiliações atuais com 100% de `ano_inicio`) |

---

## Esquema do JSON Gerado

Os documentos salvos em `curriculos_json/<Nome Completo>.json` seguem a seguinte estrutura:

```json
{
    "_id": "0616238673458322",
    "nome_completo": "Walter Ruggeri Waldman",
    "listaNomesCitacao": [
        "WALDMAN, W.",
        "WALDMAN, W. R.",
        "WALDMAN, WALTER RUGGERI"
    ],
    "endereco": "Universidade Federal de São Carlos, Campus Sorocaba...",
    "endereco_profissional": {
        "texto": "Universidade Federal de São Carlos, Campus Sorocaba...",
        "cep": "18052780",
        "municipio": "Sorocaba",
        "estado": "SP",
        "pais": "Brasil"
    },
    "locais_georreferenciamento": [
        {
            "tipo": "atual",
            "instituicao": "Universidade Federal de São Carlos, UFSCAR, Brasil.",
            "ano_inicio": 2011,
            "ano_fim": "Atual",
            "municipio": "Sorocaba",
            "estado": "SP",
            "pais": "Brasil"
        },
        {
            "tipo": "historico",
            "instituicao": "Universidade Estadual de Campinas, UNICAMP, Brasil.",
            "ano_inicio": 1999,
            "ano_fim": 2003,
            "municipio": "Campinas",
            "estado": "SP",
            "pais": "Brasil"
        }
    ],
    "area_de_atuacao": {
        "Química": [
            "ciência dos materiais",
            "ensino de química"
        ]
    },
    "linhas_pesquisa": [
        "Degradação, estabilização e reciclagem de polímeros",
        "Polímeros Biodegradáveis"
    ],
    "projetos": [
        {
            "periodo": "2022 - Atual",
            "ano_inicio": 2022,
            "ano_fim": "Atual",
            "titulo": "Materiais Avançados para recuperação e monitoramento...",
            "descricao": "Neste projeto o objetivo é o desenvolvimento e aplicação de materiais avançados...",
            "situacao": "Em andamento",
            "natureza": "Pesquisa",
            "integrantes": [
                { "nome": "Walter Ruggeri Waldman", "papel": "Integrante" },
                { "nome": "Lucia Mascaro", "papel": "Coordenador" }
            ]
        }
    ],
    "listaPB": [
        {
            "doi": "http://dx.doi.org/10.1016/j.jenvman.2024.123498",
            "titulo": "Forensic determination of adhesive vinyl microplastics in urban soils",
            "ano": 2025,
            "colaboradores": [
                { "nome": "SEBASTIÃO, GLAUCIA I.A.", "id_lattes": "" },
                { "nome": "Waldman, Walter R.", "id_lattes": "0616238673458322" }
            ],
            "texto_completo": "SEBASTIÃO, G. I. A. ; ... ; Waldman, W. R. . Forensic determination..."
        }
    ],
    "trabalhos_completos": [
        {
            "titulo": "Detecção Seletiva de Microplásticos Vinílicos em Solo",
            "ano": 2023,
            "doi": null,
            "colaboradores": [
                { "nome": "Waldman, W. R.", "id_lattes": "0616238673458322" }
            ],
            "detalhes": "In: Congresso Brasileiro de Polímeros, 2023, Joinville.",
            "texto_completo": "Waldman, W. R. . Detecção Seletiva de Microplásticos... In: ..."
        }
    ],
    "orientacoes_concluidas": [
        {
            "aluno": "Nome do Aluno",
            "titulo": "Título do Trabalho",
            "ano": "2023"
        }
    ],
    "orientacoes_em_andamento": [
        {
            "aluno": "Nome do Aluno",
            "titulo": "Título do Trabalho",
            "ano": "2024"
        }
    ]
}
```

---

## Instalação e Dependências

Recomenda-se utilizar um ambiente virtual Python (`venv`):

```bash
# Criação e ativação do ambiente virtual
python -m venv venv
.\venv\Scripts\activate   # No Windows
# source venv/bin/activate # No Linux/macOS

# Instalação das dependências essenciais
pip install beautifulsoup4 lxml spacy nltk keybert sentence-transformers umap-learn hdbscan pymongo

# Modelo de linguagem em português para spaCy
python -m spacy download pt_core_news_sm
```

---

## Guia de Execução

Execute os passos sequencialmente a partir do diretório `Parser/`:

### Passo 1: Extração, Parsing e Preenchimento Automático
Lê os arquivos HTML em `curriculos/`, extrai todos os campos estruturados em `curriculos_json/` e já executa automaticamente a resolução e vinculação dos IDs Lattes dos coautores da rede ao final:
```bash
python parser.py
```

### Passo 2: Execução Avulsa de Preenchimento de IDs (Opcional)
Caso queira rodar apenas a reconciliação de nomes e atualização de IDs Lattes sem precisar reprocessar os HTMLs:
```bash
python filling_idlattes.py --folder curriculos_json --log filled_idlattes_log.csv
```

### Passo 3: Validação Completa do Pipeline
Verifica a integridade de todos os 54 currículos e emite o relatório de conformidade:
```bash
python validar_tudo.py
```

### Passo 4: Análise de Redes, Ineditismo e Dinâmica Espacial
Processa a matriz de colaborações, identifica novas parcerias históricas e mapeia os locais dos pesquisadores no ano de publicação:
```bash
python queries.py
```

### Passo 5: Modelagem Semântica e Clusterização com PLN
Gera as keyphrases dos projetos e artigos, projeta os embeddings e detecta os clusters temáticos:
```bash
python pln_estudo.py
```

### Passo 6: Carga dos Dados no MongoDB / Atlas (Opcional)
Importa todos os documentos JSON para a coleção `pesquisadores` no banco `Rede_Colaboracao`:
```bash
python import_mongo.py
```
