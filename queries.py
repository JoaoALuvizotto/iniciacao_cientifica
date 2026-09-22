import json
import glob
import re
from datetime import datetime
from itertools import combinations
from collections import defaultdict

def carregar_dados(diretorio='curriculos_json/*.json'):
    pesquisadores = {}
    mapa_citacoes = {}
    
    # 1. Carrega todos os pesquisadores e cria um dicionário de "Nomes em Citação" -> "Nome Completo"
    for arquivo in glob.glob(diretorio):
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            nome_completo = dados.get('nome_completo')
            
            if not nome_completo:
                continue
                
            pesquisadores[nome_completo] = dados
            
            # Adiciona o próprio nome como chave de busca
            mapa_citacoes[nome_completo.strip().upper()] = nome_completo
            
            # Mapeia todas as variações de citação para o nome principal
            for nome_citacao in dados.get('listaNomesCitacao', []):
                mapa_citacoes[nome_citacao.strip().upper()] = nome_completo
                
    return pesquisadores, mapa_citacoes

def extrair_ano(texto_citacao):
    # Procura por anos de 4 dígitos (19xx ou 20xx) próximos ao final do texto
    anos = re.findall(r'\b(19\d{2}|20\d{2})\b', texto_citacao)
    return int(anos[-1]) if anos else None

def analisar_colaboracoes(pesquisadores, mapa_citacoes):
    # Lista de todas as arestas (colaborações) encontradas
    todas_colaboracoes = []
    
    for nome_pesquisador, dados in pesquisadores.items():
        artigos = dados.get('listaPB', [])
        
        for artigo in artigos:
            ano = extrair_ano(artigo.get('texto_completo', ''))
            if not ano:
                continue
                
            autores_artigo = set([nome_pesquisador])
            
            # Tenta encontrar os coautores na nossa base (Questão 2: na lista de pessoas que temos)
            for colab in artigo.get('colaboradores', []):
                nome_colab = colab.get('nome', '').strip().upper()
                
                if nome_colab in mapa_citacoes:
                    autores_artigo.add(mapa_citacoes[nome_colab])
            
            # Se houver mais de um autor da nossa base no mesmo artigo, gera os pares de colaboração
            if len(autores_artigo) > 1:
                # combinations cria pares únicos independentes da ordem (Grafo não direcionado)
                for p1, p2 in combinations(sorted(autores_artigo), 2):
                    todas_colaboracoes.append({
                        'pesquisador_1': p1,
                        'pesquisador_2': p2,
                        'ano': ano,
                        'titulo': artigo.get('titulo')
                    })
                    
    return todas_colaboracoes

def parse_historico_enderecos(lista_enderecos_historicos):
    historico_parseado = []
    ano_atual = datetime.now().year
    
    for endereco in lista_enderecos_historicos:
        # Busca padrões como "2015 - 2019", "2020 - Atual", "2010-2015"
        match = re.search(r'(\d{4})\s*-\s*(\d{4}|[Aa]tual)', endereco)
        
        if match:
            ano_inicio = int(match.group(1))
            ano_fim_str = match.group(2).lower()
            ano_fim = ano_atual if ano_fim_str == 'atual' else int(ano_fim_str)
            
            historico_parseado.append({
                'local_completo': endereco,
                'ano_inicio': ano_inicio,
                'ano_fim': ano_fim
            })
            
    return historico_parseado

def obter_local_no_ano(ano_artigo, endereco_atual, enderecos_historicos):
    historico_parseado = parse_historico_enderecos(enderecos_historicos)
    
    # 1. Tenta encontrar no histórico
    for hist in historico_parseado:
        if hist['ano_inicio'] <= ano_artigo <= hist['ano_fim']:
            return hist['local_completo']
            
    # 2. Se não encontrou no histórico e o artigo é recente, assume o endereço atual
    ano_corrente = datetime.now().year
    if ano_artigo >= (ano_corrente - 2) and endereco_atual:
        return endereco_atual + " (Inferido como Atual)"
        
    # 3. Fallback caso o Lattes do pesquisador esteja desatualizado ou sem datas claras
    return "Localização não identificada para este ano específico"

def identificar_novas_colaboracoes_e_geografia(colaboracoes, pesquisadores):
    colaboracoes_ordenadas = sorted(colaboracoes, key=lambda x: x['ano'])
    
    colaboracoes_historicas = set()
    resultados = []
    
    for colab in colaboracoes_ordenadas:
        p1 = colab['pesquisador_1']
        p2 = colab['pesquisador_2']
        ano = colab['ano']
        par = (p1, p2)
        
        # Ineditismo da colaboração
        is_nova = par not in colaboracoes_historicas
        if is_nova:
            colaboracoes_historicas.add(par)
            
        # Extração de Endereços Brutos
        end_atual_p1 = pesquisadores[p1].get('endereco', '')
        end_hist_p1 = pesquisadores[p1].get('enderecos_historicos', [])
        
        end_atual_p2 = pesquisadores[p2].get('endereco', '')
        end_hist_p2 = pesquisadores[p2].get('enderecos_historicos', [])
        
        # Geolocalização exata baseada no tempo
        local_p1_no_ano = obter_local_no_ano(ano, end_atual_p1, end_hist_p1)
        local_p2_no_ano = obter_local_no_ano(ano, end_atual_p2, end_hist_p2)
        
        resultados.append({
            'ano': ano,
            'pesquisador_1': p1,
            'pesquisador_2': p2,
            'nova_colaboracao': is_nova,
            'titulo_artigo': colab['titulo'],
            'local_p1_no_momento_da_publicacao': local_p1_no_ano,
            'local_p2_no_momento_da_publicacao': local_p2_no_ano
        })
        
    return resultados

if __name__ == "__main__":
    print("Carregando pesquisadores e mapeando citações...")
    pesquisadores, mapa_citacoes = carregar_dados()
    
    print("Extraindo arestas de colaboração...")
    colaboracoes_brutas = analisar_colaboracoes(pesquisadores, mapa_citacoes)
    
    print("Identificando ineditismo e agrupando geografia...")
    resultados_finais = identificar_novas_colaboracoes_e_geografia(colaboracoes_brutas, pesquisadores)
    
    # Exibe um resumo focado nas "Novas Colaborações"
    for res in resultados_finais:
        if res['nova_colaboracao']:
            print(f"[{res['ano']}] NOVA COLABORAÇÃO: {res['pesquisador_1']} <-> {res['pesquisador_2']}")
            print(f"    Artigo: {res['titulo_artigo']}")
            
            # Corrigido: Usando as chaves exatas que foram geradas no dicionário
            local_p1 = res.get('local_p1_no_momento_da_publicacao', 'Não informado')
            local_p2 = res.get('local_p2_no_momento_da_publicacao', 'Não informado')
            
            print(f"    Local P1: {local_p1[:70]}...")
            print(f"    Local P2: {local_p2[:70]}...\n")