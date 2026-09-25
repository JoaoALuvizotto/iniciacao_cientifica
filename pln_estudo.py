import json
import spacy
import nltk
import re
import numpy as np
from datetime import datetime
from nltk.corpus import stopwords
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
import umap
import hdbscan
from collections import Counter

# Baixar stopwords caso não tenha
# nltk.download('stopwords')

def extrair_textos_separados(caminho_json, anos_limite=5):
    """
    Extrai os textos filtrando por tempo (ex: últimos 5 anos).
    Inclui projetos, publicações, e orientações (concluídas e em andamento).
    """
    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    textos = []
    
    ano_corte = datetime.now().year - anos_limite
    
    if "linhas_pesquisa" in dados:
        textos.extend(dados["linhas_pesquisa"])
        
    if "projetos" in dados:
        for proj in dados["projetos"]:
            ano_fim_val = proj.get("ano_fim")
            ano_fim = datetime.now().year if str(ano_fim_val).lower() == "atual" else (int(ano_fim_val) if str(ano_fim_val).isdigit() else None)
            
            if ano_fim is None:
                periodo = proj.get("periodo", "")
                if "Atual" in periodo:
                    ano_fim = datetime.now().year
                else:
                    anos_encontrados = re.findall(r'\d{4}', periodo)
                    ano_fim = int(anos_encontrados[-1]) if anos_encontrados else None
                    
            if ano_fim and ano_fim >= ano_corte:
                texto_proj = proj.get("titulo", "")
                if proj.get("descricao"):
                    texto_proj = f"{texto_proj}. {proj.get('descricao')}".strip(" .")
                if texto_proj:
                    textos.append(texto_proj)
                        
    if "orientacoes_concluidas" in dados:
        for orientacao in dados["orientacoes_concluidas"]:
            ano_str = orientacao.get("ano", "0")
            if str(ano_str).isdigit() and int(ano_str) >= ano_corte:
                textos.append(orientacao.get("titulo", ""))
                
    if "orientacoes_em_andamento" in dados:
        for orientacao in dados["orientacoes_em_andamento"]:
            textos.append(orientacao.get("titulo", ""))
                
    if "listaPB" in dados:
        for pub in dados["listaPB"]:
            ano_pub = pub.get("ano")
            if not ano_pub:
                texto_comp = pub.get("texto_completo", "")
                anos_pub = re.findall(r'\b(19\d{2}|20\d{2})\b', str(texto_comp))
                if anos_pub:
                    ano_pub = int(anos_pub[-1])
            
            if ano_pub and int(ano_pub) >= ano_corte:
                textos.append(pub.get("titulo", ""))

    if "trabalhos_completos" in dados:
        for tc in dados["trabalhos_completos"]:
            if isinstance(tc, dict):
                ano_tc = tc.get("ano")
                if ano_tc and int(ano_tc) >= ano_corte:
                    textos.append(tc.get("titulo", ""))

    # Retorna os textos limpos de espaços vazios
    return [t for t in textos if t and t.strip()]

def pipeline_pln_completo(caminho_json):
    print("Carregando modelos...")
    nlp = spacy.load("pt_core_news_sm")
    kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')
    
    stop_hybrid = list(set(stopwords.words('portuguese')).union(set(stopwords.words('english'))))
    stop_hybrid.extend(['projeto', 'estudo', 'análise', 'desenvolvimento', 'abordagem', 'proposta', 'study', 'analysis', 'sobre', 'uso'])
    
    textos_individuais = extrair_textos_separados(caminho_json)
    todas_keywords = []
    
    
    for texto in textos_individuais:
        doc = nlp(texto)
        tokens_limpos = [token.text.lower() for token in doc if not token.is_punct and not token.is_digit]
        texto_limpo = " ".join(tokens_limpos)
        
        # Extrai poucas palavras por bloco para garantir relevância
        #mais palavras pode ser melhor (5)
        keywords = kw_model.extract_keywords(
            texto_limpo, 
            keyphrase_ngram_range=(2, 3), 
            stop_words=stop_hybrid,
            top_n=3,
            use_mmr=True, 
            diversity=0.7 
        )
        termos = [kw[0] for kw in keywords]
        todas_keywords.extend(termos)

    #Filtragem de frequência
    frequencias = Counter(todas_keywords)
    
    # Filtro: Mantém apenas as palavras que aparecem >= 2 vezes
    termos_frequentes_dict = {termo: freq for termo, freq in frequencias.items() if freq >= 2}
    
    # Extrai apenas a lista de strings para passar para o modelo de embeddings
    lista_termos_finais = list(termos_frequentes_dict.keys())
    
    print(f"Total de keyphrases extraídas inicialmente: {len(todas_keywords)}")
    print(f"Termos que passaram no filtro (frequentes): {len(lista_termos_finais)}\n")
    
    if len(lista_termos_finais) < 2:
        print("Erro: Não sobraram termos suficientes após o filtro para criar clusters.")
        return

    #Vetorização
    embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    embeddings = embed_model.encode(lista_termos_finais)

    #UMAP
    reducer = umap.UMAP(n_neighbors=2, n_components=5, metric='cosine', random_state=42)
    embeddings_reduzidos = reducer.fit_transform(embeddings)

    #HDBSCAN
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2, 
        metric='euclidean', 
        prediction_data=True, 
        #cluster_selection_epsilon=0.5
        )
    cluster_labels = clusterer.fit_predict(embeddings_reduzidos)

    #Resultados
    resultados = {}
    for termo, label in zip(lista_termos_finais, cluster_labels):
        if label not in resultados:
            resultados[label] = []
        resultados[label].append(termo)
        
    for cluster_id, palavras in resultados.items():
        if cluster_id == -1:
            print(f"Cluster -1 (Ruído/Termos isolados): {palavras}")
        else:
            print(f"Cluster {cluster_id}: {palavras}")

if __name__ == "__main__":
    caminho = 'curriculos_json/Sahudy Montenegro González.json' 
    pipeline_pln_completo(caminho)