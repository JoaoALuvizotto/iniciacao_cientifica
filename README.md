# Módulo Parser

Componente central do pipeline para extração, reconciliação de entidades, modelagem de redes e clusterização semântica sobre dados da Plataforma Lattes.

Para a documentação completa de todo o projeto, consulte o [README.md da raiz](../README.md).

---

## Componentes

- **`parser.py`**: Parser estrutural baseado em BeautifulSoup/lxml para processamento dos HTMLs em `curriculos/` e emissão dos documentos em `curriculos_json/`.
- **`filling_idlattes.py`**: Algoritmo determinístico de resolução de entidades para coautores presentes em `listaPB`, com geração de trilha de auditoria em `filled_idlattes_log.csv`.
- **`queries.py`**: Algoritmos de inferência de redes de coautoria, ineditismo de parcerias e mapeamento temporal da afiliação institucional.
- **`import_mongo.py`**: Carga em lote dos documentos JSON para coleções MongoDB.
- **`pln_estudo.py`**: Pipeline não supervisionado de modelagem de tópicos: extração via KeyBERT, geração de embeddings densos com SentenceTransformers, redução de dimensionalidade por UMAP e clusterização baseada em densidade por HDBSCAN.
- **`pln.py` / `teste_pln.py`**: Rotinas de validação de lematização e anotação morfossintática via spaCy (`pt_core_news_sm`).
- **`arquivo IDs lattes.txt`**: Catálogo de controle de IDs Lattes monitorados (16 dígitos).
- **`curriculos/`**: Diretório de entrada com arquivos HTML brutos indexados pelo ID Lattes.
- **`curriculos_json/`**: Repositório de documentos JSON estruturados e reconciliados.

---

## Execução

```bash
# 1. Parsing dos arquivos HTML brutos
python parser.py

# 2. Resolução de entidades e enriquecimento de coautores
python filling_idlattes.py --folder curriculos_json --log filled_idlattes_log.csv

# 3. Análise de grafos de colaboração e dinâmica temporal
python queries.py

# 4. Pipeline de extração e clusterização semântica (NLP)
python pln_estudo.py

# 5. Carga de documentos para o MongoDB
python import_mongo.py
```
