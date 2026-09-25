from collections import defaultdict
from bs4 import BeautifulSoup
import re
import json
import os
import unicodedata

class LattesParser:

    # Mapeamento geográfico de instituições para agilizar e enriquecer o georreferenciamento
    INSTITUICOES_GEO = {
        'UFSCAR': ('São Carlos', 'SP', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE SÃO CARLOS': ('São Carlos', 'SP', 'Brasil'),
        'UNICAMP': ('Campinas', 'SP', 'Brasil'),
        'UNIVERSIDADE ESTADUAL DE CAMPINAS': ('Campinas', 'SP', 'Brasil'),
        'USP': ('São Paulo', 'SP', 'Brasil'),
        'UNIVERSIDADE DE SÃO PAULO': ('São Paulo', 'SP', 'Brasil'),
        'UNESP': ('São Paulo', 'SP', 'Brasil'),
        'UNIVERSIDADE ESTADUAL PAULISTA': ('São Paulo', 'SP', 'Brasil'),
        'UFABC': ('Santo André', 'SP', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO ABC': ('Santo André', 'SP', 'Brasil'),
        'UNIFESP': ('São Paulo', 'SP', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE SÃO PAULO': ('São Paulo', 'SP', 'Brasil'),
        'UNIMEP': ('Piracicaba', 'SP', 'Brasil'),
        'UNIVERSIDADE METODISTA DE PIRACICABA': ('Piracicaba', 'SP', 'Brasil'),
        'USF': ('Bragança Paulista', 'SP', 'Brasil'),
        'UNIVERSIDADE SÃO FRANCISCO': ('Bragança Paulista', 'SP', 'Brasil'),
        'UNIARA': ('Araraquara', 'SP', 'Brasil'),
        'UNIVERSIDADE DE ARARAQUARA': ('Araraquara', 'SP', 'Brasil'),
        'UNIABC': ('Santo André', 'SP', 'Brasil'),
        'UNIVERSIDADE DO GRANDE ABC': ('Santo André', 'SP', 'Brasil'),
        'PUC-SP': ('São Paulo', 'SP', 'Brasil'),
        'PUCSP': ('São Paulo', 'SP', 'Brasil'),
        'PONTIFÍCIA UNIVERSIDADE CATÓLICA DE SÃO PAULO': ('São Paulo', 'SP', 'Brasil'),
        'ITAL': ('Campinas', 'SP', 'Brasil'),
        'INSTITUTO DE TECNOLOGIA DE ALIMENTOS': ('Campinas', 'SP', 'Brasil'),
        'CNPEM': ('Campinas', 'SP', 'Brasil'),
        'CENTRO NACIONAL DE PESQUISA EM ENERGIA E MATERIAIS': ('Campinas', 'SP', 'Brasil'),
        'LNLS': ('Campinas', 'SP', 'Brasil'),
        'EMBRAPA': ('São Carlos', 'SP', 'Brasil'),
        'EMPRESA BRASILEIRA DE PESQUISA AGROPECUÁRIA': ('São Carlos', 'SP', 'Brasil'),
        'IPT': ('São Paulo', 'SP', 'Brasil'),
        'IPEN': ('São Paulo', 'SP', 'Brasil'),
        'INPE': ('São José dos Campos', 'SP', 'Brasil'),
        'PREFEITURA MUNICIPAL DE SÃO CARLOS': ('São Carlos', 'SP', 'Brasil'),
        'UENF': ('Campos dos Goytacazes', 'RJ', 'Brasil'),
        'UNIVERSIDADE ESTADUAL DO NORTE FLUMINENSE': ('Campos dos Goytacazes', 'RJ', 'Brasil'),
        'UFRJ': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO RIO DE JANEIRO': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'UFF': ('Niterói', 'RJ', 'Brasil'),
        'UNIVERSIDADE FEDERAL FLUMINENSE': ('Niterói', 'RJ', 'Brasil'),
        'UERJ': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'UNIVERSIDADE DO ESTADO DO RIO DE JANEIRO': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'UFRRJ': ('Seropédica', 'RJ', 'Brasil'),
        'UNIVERSIDADE FEDERAL RURAL DO RIO DE JANEIRO': ('Seropédica', 'RJ', 'Brasil'),
        'UNIRIO': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'UNESA': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'UNIVERSIDADE ESTÁCIO DE SÁ': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'UNIGRANRIO': ('Duque de Caxias', 'RJ', 'Brasil'),
        'UNIVERSIDADE DO GRANDE RIO': ('Duque de Caxias', 'RJ', 'Brasil'),
        'PUC-RIO': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'PONTIFÍCIA UNIVERSIDADE CATÓLICA DO RIO DE JANEIRO': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'PETROBRAS': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'PETRÓLEO BRASILEIRO': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'TRANSPETRO': ('Rio de Janeiro', 'RJ', 'Brasil'),
        'UFMG': ('Belo Horizonte', 'MG', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE MINAS GERAIS': ('Belo Horizonte', 'MG', 'Brasil'),
        'UFU': ('Uberlândia', 'MG', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE UBERLÂNDIA': ('Uberlândia', 'MG', 'Brasil'),
        'UFLA': ('Lavras', 'MG', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE LAVRAS': ('Lavras', 'MG', 'Brasil'),
        'UFV': ('Viçosa', 'MG', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE VIÇOSA': ('Viçosa', 'MG', 'Brasil'),
        'UFOP': ('Ouro Preto', 'MG', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE OURO PRETO': ('Ouro Preto', 'MG', 'Brasil'),
        'UNIFEI': ('Itajubá', 'MG', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE ITAJUBÁ': ('Itajubá', 'MG', 'Brasil'),
        'UNIFAL': ('Alfenas', 'MG', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE ALFENAS': ('Alfenas', 'MG', 'Brasil'),
        'PREFEITURA MUNICIPAL DE BELO HORIZONTE': ('Belo Horizonte', 'MG', 'Brasil'),
        'UFPR': ('Curitiba', 'PR', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO PARANÁ': ('Curitiba', 'PR', 'Brasil'),
        'UEM': ('Maringá', 'PR', 'Brasil'),
        'UNIVERSIDADE ESTADUAL DE MARINGÁ': ('Maringá', 'PR', 'Brasil'),
        'UEL': ('Londrina', 'PR', 'Brasil'),
        'UNIVERSIDADE ESTADUAL DE LONDRINA': ('Londrina', 'PR', 'Brasil'),
        'UEPG': ('Ponta Grossa', 'PR', 'Brasil'),
        'UNIVERSIDADE ESTADUAL DE PONTA GROSSA': ('Ponta Grossa', 'PR', 'Brasil'),
        'UFSC': ('Florianópolis', 'SC', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE SANTA CATARINA': ('Florianópolis', 'SC', 'Brasil'),
        'FURB': ('Blumenau', 'SC', 'Brasil'),
        'UNIVERSIDADE REGIONAL DE BLUMENAU': ('Blumenau', 'SC', 'Brasil'),
        'UNESC': ('Criciúma', 'SC', 'Brasil'),
        'UNIVERSIDADE DO EXTREMO SUL CATARINENSE': ('Criciúma', 'SC', 'Brasil'),
        'UFRGS': ('Porto Alegre', 'RS', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO RIO GRANDE DO SUL': ('Porto Alegre', 'RS', 'Brasil'),
        'UFPEL': ('Pelotas', 'RS', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE PELOTAS': ('Pelotas', 'RS', 'Brasil'),
        'UFSM': ('Santa Maria', 'RS', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE SANTA MARIA': ('Santa Maria', 'RS', 'Brasil'),
        'UCS': ('Caxias do Sul', 'RS', 'Brasil'),
        'UNIVERSIDADE DE CAXIAS DO SUL': ('Caxias do Sul', 'RS', 'Brasil'),
        'UNISC': ('Santa Cruz do Sul', 'RS', 'Brasil'),
        'UNIVERSIDADE DE SANTA CRUZ DO SUL': ('Santa Cruz do Sul', 'RS', 'Brasil'),
        'UNIPAMPA': ('Bagé', 'RS', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO PAMPA': ('Bagé', 'RS', 'Brasil'),
        'FURG': ('Rio Grande', 'RS', 'Brasil'),
        'PUCRS': ('Porto Alegre', 'RS', 'Brasil'),
        'PONTIFÍCIA UNIVERSIDADE CATÓLICA DO RIO GRANDE DO SUL': ('Porto Alegre', 'RS', 'Brasil'),
        'UNISINOS': ('São Leopoldo', 'RS', 'Brasil'),
        'UFBA': ('Salvador', 'BA', 'Brasil'),
        'UNIVERSIDADE FEDERAL DA BAHIA': ('Salvador', 'BA', 'Brasil'),
        'UEFS': ('Feira de Santana', 'BA', 'Brasil'),
        'UNIVERSIDADE ESTADUAL DE FEIRA DE SANTANA': ('Feira de Santana', 'BA', 'Brasil'),
        'CIMATEC': ('Salvador', 'BA', 'Brasil'),
        'UNIVERSIDADE SENAI CIMATEC': ('Salvador', 'BA', 'Brasil'),
        'UFPE': ('Recife', 'PE', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE PERNAMBUCO': ('Recife', 'PE', 'Brasil'),
        'UFPB': ('João Pessoa', 'PB', 'Brasil'),
        'UNIVERSIDADE FEDERAL DA PARAÍBA': ('João Pessoa', 'PB', 'Brasil'),
        'UFC': ('Fortaleza', 'CE', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO CEARÁ': ('Fortaleza', 'CE', 'Brasil'),
        'UECE': ('Fortaleza', 'CE', 'Brasil'),
        'UNIVERSIDADE ESTADUAL DO CEARÁ': ('Fortaleza', 'CE', 'Brasil'),
        'UFAL': ('Maceió', 'AL', 'Brasil'),
        'UNIVERSIDADE FEDERAL DE ALAGOAS': ('Maceió', 'AL', 'Brasil'),
        'UFRN': ('Natal', 'RN', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO RIO GRANDE DO NORTE': ('Natal', 'RN', 'Brasil'),
        'UFMA': ('São Luís', 'MA', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO MARANHÃO': ('São Luís', 'MA', 'Brasil'),
        'UFPI': ('Teresina', 'PI', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO PIAUÍ': ('Teresina', 'PI', 'Brasil'),
        'UNIT': ('Aracaju', 'SE', 'Brasil'),
        'UNIVERSIDADE TIRADENTES': ('Aracaju', 'SE', 'Brasil'),
        'UNB': ('Brasília', 'DF', 'Brasil'),
        'UNIVERSIDADE DE BRASÍLIA': ('Brasília', 'DF', 'Brasil'),
        'UFT': ('Palmas', 'TO', 'Brasil'),
        'UNIVERSIDADE FEDERAL DO TOCANTINS': ('Palmas', 'TO', 'Brasil'),
        'UNEMAT': ('Cáceres', 'MT', 'Brasil'),
        'UNIVERSIDADE DO ESTADO DE MATO GROSSO': ('Cáceres', 'MT', 'Brasil'),
        'IFAM': ('Manaus', 'AM', 'Brasil'),
        'UEA': ('Manaus', 'AM', 'Brasil'),
        'UNIVERSIDADE DO ESTADO DO AMAZONAS': ('Manaus', 'AM', 'Brasil'),
        'FUB': ('Berlim', 'Berlim', 'Alemanha'),
        'FREIE UNIVERSITÄT BERLIN': ('Berlim', 'Berlim', 'Alemanha'),
        'TUBERLIN': ('Berlim', 'Berlim', 'Alemanha'),
        'TECHNISCHE UNIVERSITÄT BERLIN': ('Berlim', 'Berlim', 'Alemanha'),
        'MPIP': ('Mainz', 'Renânia-Palatinado', 'Alemanha'),
        'MAX PLANCK': ('Mainz', 'Renânia-Palatinado', 'Alemanha'),
        'POLIMI': ('Milão', 'Lombardia', 'Itália'),
        'POLITECNICO DI MILANO': ('Milão', 'Lombardia', 'Itália'),
        'UNIPI': ('Pisa', 'Toscana', 'Itália'),
        'UNIVERSITÀ DI PISA': ('Pisa', 'Toscana', 'Itália'),
        'UNIBO': ('Bolonha', 'Emília-Romanha', 'Itália'),
        'UNIVERSITÀ DI BOLOGNA': ('Bolonha', 'Emília-Romanha', 'Itália'),
        'UNIBA': ('Bari', 'Apúlia', 'Itália'),
        'UC': ('Coimbra', 'Coimbra', 'Portugal'),
        'UNIVERSIDADE DE COIMBRA': ('Coimbra', 'Coimbra', 'Portugal'),
        'UPORTO': ('Porto', 'Porto', 'Portugal'),
        'UNIVERSIDADE DO PORTO': ('Porto', 'Porto', 'Portugal'),
        'UMINHO': ('Braga', 'Braga', 'Portugal'),
        'UNIVERSIDADE DO MINHO': ('Braga', 'Braga', 'Portugal'),
        'CAM': ('Cambridge', 'Inglaterra', 'Inglaterra'),
        'UNIVERSITY OF CAMBRIDGE': ('Cambridge', 'Inglaterra', 'Inglaterra'),
        'BIRMINGHAM': ('Birmingham', 'Inglaterra', 'Inglaterra'),
        'UNIVERSITY OF BIRMINGHAM': ('Birmingham', 'Inglaterra', 'Inglaterra'),
        'YORK': ('York', 'Inglaterra', 'Inglaterra'),
        'UNIVERSITY OF YORK': ('York', 'Inglaterra', 'Inglaterra'),
        'KCL': ('Londres', 'Inglaterra', 'Grã-Bretanha'),
        'MIT': ('Cambridge', 'Massachusetts', 'Estados Unidos'),
        'MASSACHUSETTS INSTITUTE OF TECHNOLOGY': ('Cambridge', 'Massachusetts', 'Estados Unidos'),
        'OSAKAU': ('Osaka', 'Osaka', 'Japão'),
        'OSAKA UNIVERSITY': ('Osaka', 'Osaka', 'Japão')
    }

    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.data = {}

    @staticmethod
    def normalizar_nome(nome: str) -> str:
        """
        Padroniza nomes de pessoas para comparação exata de coautoria:
        - Remove acentuação via decomposição Unicode (NFKD)
        - Converte para maiúsculas
        - Mantém apenas caracteres alfanuméricos A-Z e 0-9
        """
        if not nome:
            return ""
        nfkd = unicodedata.normalize('NFKD', nome.upper())
        sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return re.sub(r'[^A-Z0-9]', '', sem_acento)

    @staticmethod
    def limpar_texto(texto: str) -> str:
        """
        Remove ruídos de formatação e corrige anomalias de codificação do Lattes:
        - Converte sequências de espaços e quebras de linha em espaço único
        - Normaliza '?' espúrios gerados por conversão de en-dash/em-dash no CNPq (ex: 'WCAMA 2014 ? V Workshop' -> 'WCAMA 2014 - V Workshop')
        - Corrige '?' que substituíram aspas em nomes próprios (ex: '?PAMDA?' -> '"PAMDA"')
        """
        if not texto:
            return ""
        texto = re.sub(r'\s+', ' ', texto)
        texto = re.sub(r'(\b\d{4})\s*\?\s*([A-Z\d])', r'\1 - \2', texto)
        texto = re.sub(r'\?([A-Za-z0-9_-]+)\?', r'"\1"', texto)
        return texto.strip()

    @staticmethod
    def extrair_geo_endereco_texto(texto: str):
        """
        Extrai município, estado (UF) e país de cadeias de endereço no formato Lattes:
        Exemplo: '... 18052780 - Sorocaba, SP - Brasil' -> ('Sorocaba', 'SP', 'Brasil')
        """
        if not texto:
            return None, None, None
        m = re.search(r'(?:(?:CEP:?\s*)?\d{5}-?\d{3}\s*[-–,]\s*)?([A-Za-zÀ-ÿ\s\.\']+),\s*([A-Z]{2})\b(?:\s*[-–]\s*([A-Za-zÀ-ÿ]+))?', texto)
        if m:
            cidade = m.group(1).strip(" ,.-")
            uf = m.group(2).strip()
            pais = m.group(3).strip() if m.group(3) else "Brasil"
            return cidade, uf, pais
        return None, None, None

    def resolver_geo_instituicao(self, nome_inst: str, contexto_atividades: str = ""):
        """
        Determina o município e estado da instituição histórica a partir de:
        1. Menção explícita de Campus nas atividades (ex: 'Campus Sorocaba')
        2. Dicionário institucional catalogado
        3. Padrão de endereço no nome da instituição
        4. País estrangeiro indicado ao final da linha
        """
        # 1. Verifica campus específico nas atividades
        if contexto_atividades:
            m_campus = re.search(r'Campus\s+([A-Za-zÀ-ÿ\s]+?)(?:,|$|\.)', contexto_atividades, re.IGNORECASE)
            if m_campus:
                campus_cidade = m_campus.group(1).strip()
                if len(campus_cidade) > 2 and not any(k in campus_cidade.lower() for k in ['universit', 'central', 'sede']):
                    cidade_ext, uf_ext, _ = self.extrair_geo_endereco_texto(contexto_atividades)
                    if not uf_ext:
                        m_uf = re.search(r'\b([A-Z]{2})\b', nome_inst)
                        uf_ext = m_uf.group(1) if m_uf else "SP"
                    return campus_cidade, uf_ext, "Brasil"

        # 2. Busca no catálogo de instituições conhecidas
        nfkd = unicodedata.normalize('NFKD', nome_inst.upper())
        norm_inst = "".join([c for c in nfkd if not unicodedata.combining(c)])
        norm_inst = re.sub(r'[^A-Z0-9]', ' ', norm_inst)
        
        for key, (cid, uf, pais) in self.INSTITUICOES_GEO.items():
            key_nfkd = "".join([c for c in unicodedata.normalize('NFKD', key.upper()) if not unicodedata.combining(c)])
            key_norm = re.sub(r'[^A-Z0-9]', ' ', key_nfkd)
            if re.search(r'\b' + re.escape(key_norm) + r'\b', norm_inst):
                return cid, uf, pais

        # 3. Extração genérica de padrão de cidade/UF
        cidade, uf, pais = self.extrair_geo_endereco_texto(nome_inst)
        if cidade and uf:
            return cidade, uf, pais

        # 4. Detecção de país estrangeiro
        m_pais = re.search(r',\s*([A-Za-zÀ-ÿ\s]+)\.\s*$', nome_inst)
        if m_pais:
            pais_nome = m_pais.group(1).strip()
            if pais_nome not in ['Brasil', 'Brazil']:
                return None, None, pais_nome

        return None, None, "Brasil"

    # Extrai o nome completo do pesquisador.
    def extract_name(self):
        try:
            nome_tag = self.soup.find('h2', class_='nome')
            self.data['nome_completo'] = nome_tag.text.strip() if nome_tag else None
        except Exception as e:
            print(f"Erro ao extrair nome: {e}")
            self.data['nome_completo'] = None

    # Extrai o ID Lattes de 16 dígitos.
    def extract_lattes_id(self):
        try:
            id_tag = self.soup.find('span', style='font-weight: bold; color: #326C99;')
            self.data['_id'] = id_tag.text.strip() if id_tag else None
        except Exception as e:
            print(f"Erro ao extrair ID Lattes: {e}")
            self.data['_id'] = None

    # Extrai nomes em citações bibliográficas.
    def extract_citation_names(self):
        try:
            nomes_tag = self.soup.find('b', string=re.compile(r'Nome em citações bibliográficas'))
            if nomes_tag:
                parent_div = nomes_tag.find_parent('div', class_='layout-cell-3')
                sibling_div = parent_div.find_next_sibling('div', class_='layout-cell-9') if parent_div else None
                nomes_brutos = sibling_div.get_text(strip=True) if sibling_div else ""
                nomes_limpos = self.limpar_texto(nomes_brutos)
                lista_nomes = [nome.strip() for nome in nomes_limpos.split(';') if nome.strip()]
                self.data['listaNomesCitacao'] = sorted(list(set(lista_nomes)))
            else:
                self.data['listaNomesCitacao'] = []
        except Exception as e:
            print(f"Erro ao extrair nomes de citação: {e}")
            self.data['listaNomesCitacao'] = []

    # Extrai o endereço profissional atual e estrutura dados para georreferenciamento.
    def extract_address(self):
        try:
            endereco_tag = self.soup.find('b', string=re.compile(r'Endereço Profissional'))
            if not endereco_tag:
                self.data['endereco'] = None
                self.data['endereco_profissional'] = None
                return

            endereco_pai = endereco_tag.find_parent('div', class_='layout-cell-3')
            endereco_cell = endereco_pai.find_next_sibling('div', class_='layout-cell-9') if endereco_pai else None
            
            if endereco_cell:
                for br in endereco_cell.find_all('br'):
                    br.replace_with(', ')
                
                texto = endereco_cell.get_text(separator=' ', strip=True)
                texto = re.sub(r'\s+', ' ', texto)
                texto = texto.replace(':,', ':').replace(', ,', ',')
                texto_limpo = self.limpar_texto(texto)
                
                self.data['endereco'] = texto_limpo
                
                # Extrai município, UF, CEP e país estruturados
                m_geo = re.search(r'(?:(?:CEP:?\s*)?(\d{5}-?\d{3})\s*[-–,]\s*)?([A-Za-zÀ-ÿ\s\.\']+),\s*([A-Z]{2})\b(?:\s*[-–]\s*([A-Za-zÀ-ÿ]+))?', texto_limpo)
                if m_geo:
                    cep = m_geo.group(1) or ""
                    cidade = m_geo.group(2).strip(" ,.-")
                    uf = m_geo.group(3).strip()
                    pais = m_geo.group(4).strip() if m_geo.group(4) else "Brasil"
                    self.data['endereco_profissional'] = {
                        'texto': texto_limpo,
                        'cep': cep,
                        'municipio': cidade,
                        'estado': uf,
                        'pais': pais
                    }
                else:
                    self.data['endereco_profissional'] = {
                        'texto': texto_limpo,
                        'cep': '',
                        'municipio': '',
                        'estado': '',
                        'pais': 'Brasil'
                    }
            else:
                self.data['endereco'] = None
                self.data['endereco_profissional'] = None

        except Exception as e:
            print(f"Erro ao extrair endereço: {e}")
            self.data['endereco'] = None
            self.data['endereco_profissional'] = None

    # Extrai o histórico de afiliações a partir de 'Atuação Profissional' e constrói o georreferenciamento.
    def extract_historical_addresses(self):
        try:
            enderecos_historicos = []
            locais_georref = []
            
            # Adiciona o endereço atual como âncora nos locais de georreferenciamento
            if self.data.get('endereco_profissional') and self.data['endereco_profissional'].get('municipio'):
                end_p = self.data['endereco_profissional']
                locais_georref.append({
                    'tipo': 'atual',
                    'instituicao': self.data.get('endereco', '').split(',')[0].strip(),
                    'ano_inicio': None,
                    'ano_fim': 'Atual',
                    'municipio': end_p['municipio'],
                    'estado': end_p['estado'],
                    'pais': end_p['pais']
                })
            
            ancora = self.soup.find('a', attrs={'name': 'AtuacaoProfissional'})
            if ancora:
                wrapper = ancora.find_parent('div', class_='title-wrapper')
                if wrapper:
                    inst_blocks = wrapper.find_all('div', class_='inst_back')
                    for inst_div in inst_blocks:
                        nome_inst = self.limpar_texto(inst_div.get_text(strip=True))
                        
                        curr = inst_div.find_next_sibling('div')
                        contexto = []
                        periodos = []
                        vinculos = []
                        
                        while curr and 'inst_back' not in curr.get('class', []):
                            texto_curr = self.limpar_texto(curr.get_text(separator=' ', strip=True))
                            if texto_curr:
                                contexto.append(texto_curr)
                                for m in re.finditer(r'\b(\d{4})\s*-\s*(\d{4}|Atual)\b', texto_curr, re.IGNORECASE):
                                    periodos.append((int(m.group(1)), m.group(2).strip()))
                                if "Vínculo:" in texto_curr or "Enquadramento Funcional:" in texto_curr or "Vinculo:" in texto_curr:
                                    vinculos.append(texto_curr)
                            curr = curr.find_next_sibling('div')
                            
                        ctx_str = " ".join(contexto)
                        cidade, uf, pais = self.resolver_geo_instituicao(nome_inst, ctx_str)
                        
                        if periodos:
                            anos_ini = [p[0] for p in periodos]
                            ano_inicio = min(anos_ini)
                            tem_atual = any(p[1].lower() == 'atual' for p in periodos)
                            if tem_atual:
                                ano_fim = 'Atual'
                            else:
                                anos_fim = [int(p[1]) for p in periodos if p[1].isdigit()]
                                ano_fim = max(anos_fim) if anos_fim else ano_inicio
                        else:
                            ano_inicio = None
                            ano_fim = None
                            
                        periodo_str = f"{ano_inicio} - {ano_fim}" if ano_inicio else ""
                        
                        item_historico = {
                            'instituicao': nome_inst,
                            'periodo': periodo_str,
                            'ano_inicio': ano_inicio,
                            'ano_fim': ano_fim,
                            'vinculo': vinculos[0] if vinculos else "",
                            'municipio': cidade or "",
                            'estado': uf or "",
                            'pais': pais or "Brasil"
                        }
                        enderecos_historicos.append(item_historico)
                        
                        locais_georref.append({
                            'tipo': 'historico',
                            'instituicao': nome_inst,
                            'ano_inicio': ano_inicio,
                            'ano_fim': ano_fim,
                            'municipio': cidade or "",
                            'estado': uf or "",
                            'pais': pais or "Brasil"
                        })
            
            self.data['enderecos_historicos'] = enderecos_historicos
            self.data['locais_georreferenciamento'] = locais_georref

        except Exception as e:
            print(f"Erro ao extrair endereços históricos: {e}")
            self.data['enderecos_historicos'] = []
            self.data['locais_georreferenciamento'] = []

    # Extrai áreas e subáreas de atuação.
    def extract_activity(self):
        try:
            activity_tag = self.soup.find('h1', string=re.compile(r'Áreas de atuação'))
            if not activity_tag:
                self.data['area_de_atuacao'] = None
                return
            
            pai_tag = activity_tag.find_parent('div', class_='title-wrapper')
            activity_pai = pai_tag.find('div', class_='data-cell') if pai_tag else None
            if not activity_pai:
                activity_pai = pai_tag
                
            activities = activity_pai.find_all('div', class_='layout-cell-9') if activity_pai else []
            areas = defaultdict(list)
            for area in activities:
                texto_area = area.get_text(strip=True)
                palavra_chave = r'\s+/\s+Área:\s+'
                if not re.search(palavra_chave, texto_area):
                    continue
                partes = re.split(palavra_chave, texto_area, maxsplit=2)
                segunda_parte = partes[1].strip()
                palavra_chave2 = r'\s+/\s+Subárea:\s+'
                partes2 = re.split(palavra_chave2, segunda_parte)
                chave_area = partes2[0]
                chave_area = re.sub(r'\.', '', chave_area).strip()
                if len(partes2) > 1:
                    valor_subarea = partes2[1]
                    valor_subarea = re.sub(r'\s+', ' ', valor_subarea)
                    valor_subarea = re.sub(r'\.', ' ', valor_subarea).strip()
                    if valor_subarea not in areas[chave_area]:
                        areas[chave_area].append(valor_subarea)
                else:
                    if chave_area not in areas:
                        areas[chave_area] = []
                
            self.data['area_de_atuacao'] = dict(areas)
        except Exception as e:
            print(f"Erro ao extrair as áreas de atuação: {e}")
            self.data['area_de_atuacao'] = None

    # Processa a citação de um artigo completo, extraindo colaboradores, ano, título e IDs Lattes diretos.
    def processar_citacao_artigo(self, html_cell):
        # 1. Extração do ano da ordenação nativa do Lattes
        ano = None
        ano_tag = html_cell.find('span', class_='informacao-artigo', attrs={'data-tipo-ordenacao': 'ano'})
        if ano_tag and ano_tag.get_text(strip=True).isdigit():
            ano = int(ano_tag.get_text(strip=True))

        # 2. Mapeamento de links com IDs Lattes de 16 dígitos nos coautores
        lattes_links = {}
        for a in html_cell.find_all('a', href=True):
            href = a['href']
            m = re.search(r'lattes\.cnpq\.br/(\d{16})', href)
            if m:
                nome_a = a.get_text(strip=True)
                if nome_a:
                    lattes_links[self.normalizar_nome(nome_a)] = m.group(1)

        # 3. Limpeza de spans auxiliares sem perder o conteúdo principal
        c_copy = BeautifulSoup(str(html_cell), 'lxml')
        for info in c_copy.find_all('span', class_='informacao-artigo'):
            info.decompose()
        for citado in c_copy.find_all('span', class_='citado'):
            citado.decompose()
        for img in c_copy.find_all('img'):
            img.decompose()
            
        texto_completo = c_copy.get_text(separator=' ', strip=True)
        texto_completo = self.limpar_texto(texto_completo)
        texto_limpo = re.sub(r'[\.,\s:-]+$', '.', texto_completo)
        
        # Se ano ainda não obtido da tag, tenta regex no final do texto da citação
        if not ano:
            anos = re.findall(r'\b(19\d{2}|20\d{2})\b', texto_limpo)
            if anos:
                ano = int(anos[-1])
        
        partes = re.split(r'(?:\s\.\s|\.\.\s)', texto_limpo, maxsplit=1)
        colaboradores = []
        titulo_artigo = "Título não identificado"

        if len(partes) > 1:
            bloco_autores = partes[0].strip()
            resto = partes[1].strip()
            
            for autor in bloco_autores.split(';'):
                nome_limpo = autor.strip()
                if nome_limpo:
                    norm = self.normalizar_nome(nome_limpo)
                    id_colab = lattes_links.get(norm, "")
                    colaboradores.append({"nome": nome_limpo, "id_lattes": id_colab})
            
            partes_resto = re.split(r'\.\s', resto, maxsplit=1)
            if partes_resto:
                titulo_artigo = partes_resto[0].strip()
        else:
            norm = self.normalizar_nome(texto_limpo)
            id_colab = lattes_links.get(norm, "")
            colaboradores.append({"nome": texto_limpo, "id_lattes": id_colab})

        return colaboradores, titulo_artigo, ano, texto_limpo

    # Extrai artigos publicados em periódicos (listaPB) com ano e coautores estruturados.
    def extract_articles(self):
        try:
            articles_tags = self.soup.find_all('div', class_='artigo-completo')
            if not articles_tags:
                self.data['listaPB'] = []
                return

            lista_artigos = []
            for artigo in articles_tags:
                artigo_tag = artigo.find('div', class_='layout-cell-11')
                if not artigo_tag:
                    continue

                doi_tag = artigo_tag.find('a', class_='icone-doi')
                link_doi = doi_tag['href'] if doi_tag else None
                
                colaboradores, titulo, ano, texto_limpo = self.processar_citacao_artigo(artigo_tag)
                
                dados_artigo = {
                    'doi': link_doi,
                    'titulo': titulo,
                    'ano': ano,
                    'colaboradores': colaboradores,
                    'texto_completo': texto_limpo
                }
                lista_artigos.append(dados_artigo)
            
            self.data['listaPB'] = lista_artigos
            if 'artigos' in self.data:
                del self.data['artigos']
        except Exception as e:
            print(f"Erro ao extrair artigos publicados: {e}")
            self.data['listaPB'] = []
            self.data['artigos'] = None

    # Processa uma célula de produção em anais de congresso ou periódicos para formato estruturado.
    def processar_item_producao(self, cell):
        doi_tag = cell.find('a', class_='icone-doi')
        link_doi = doi_tag['href'] if doi_tag else None
        
        lattes_links = {}
        for a in cell.find_all('a', href=True):
            m = re.search(r'lattes\.cnpq\.br/(\d{16})', a['href'])
            if m:
                nome_a = a.get_text(strip=True)
                if nome_a:
                    lattes_links[self.normalizar_nome(nome_a)] = m.group(1)
                    
        c_copy = BeautifulSoup(str(cell), 'lxml')
        for tag in c_copy.find_all(['img']):
            tag.decompose()
        for tag in c_copy.find_all('span', class_='informacao-artigo'):
            tag.decompose()
        for tag in c_copy.find_all('span', class_='citado'):
            tag.decompose()
            
        texto = c_copy.get_text(separator=' ', strip=True)
        texto = self.limpar_texto(texto)
        texto_limpo = re.sub(r'[\.,\s:-]+$', '.', texto)
        
        anos = re.findall(r'\b(19\d{2}|20\d{2})\b', texto_limpo)
        ano = int(anos[-1]) if anos else None
        
        partes = re.split(r'(?:\s\.\s|\.\.\s)', texto_limpo, maxsplit=1)
        colaboradores = []
        titulo = ""
        detalhes = ""
        
        if len(partes) > 1:
            bloco_autores = partes[0].strip()
            resto = partes[1].strip()
            for autor in bloco_autores.split(';'):
                nome_limpo = autor.strip()
                if nome_limpo:
                    norm = self.normalizar_nome(nome_limpo)
                    id_colab = lattes_links.get(norm, "")
                    colaboradores.append({"nome": nome_limpo, "id_lattes": id_colab})
            
            m_in = re.search(r'\.\s+In:\s+', resto, re.IGNORECASE)
            if m_in:
                titulo = resto[:m_in.start()].strip()
                detalhes = resto[m_in.end():].strip()
            else:
                resto_partes = re.split(r'\.\s+', resto, maxsplit=1)
                titulo = resto_partes[0].strip()
                if len(resto_partes) > 1:
                    detalhes = resto_partes[1].strip()
        else:
            titulo = texto_limpo
            norm = self.normalizar_nome(texto_limpo)
            id_colab = lattes_links.get(norm, "")
            colaboradores.append({"nome": texto_limpo, "id_lattes": id_colab})
            
        return {
            'titulo': titulo,
            'ano': ano,
            'doi': link_doi,
            'colaboradores': colaboradores,
            'detalhes': detalhes,
            'texto_completo': texto_limpo
        }

    # Extrai produções genéricas e anais de congressos em objetos estruturados.
    def extract_generic_productions(self, target):
        if isinstance(target, str):
            encontrado = self.soup.find('a', attrs={'name': target})
            if not encontrado:
                return []
            producao_tag = encontrado.find_parent('b')
            if not producao_tag:
                return []
            producao_pai = producao_tag.find_parent('div', class_='cita-artigos')
            sibling = producao_pai.find_next_sibling('div') if producao_pai else None
        else:
            sibling = target.find_next_sibling('div')
            
        producoes = []
        while sibling:
            classes_producoes = sibling.get('class', [])
            if 'cita-artigos' in classes_producoes or 'inst_back' in classes_producoes:
                break
            if 'layout-cell-11' in classes_producoes: 
                item_dados = self.processar_item_producao(sibling)
                producoes.append(item_dados)
            sibling = sibling.find_next_sibling('div')
        
        return producoes

    def extract_productions(self):
        revistas = self.extract_generic_productions('TextosJornaisRevistas') 
        self.data['producao_revistas'] = revistas
        
        todas_ancoras = self.soup.find_all('a', attrs={'name': 'TrabalhosPublicadosAnaisCongresso'})
        for ancora in todas_ancoras:
            tag_b = ancora.find_parent('b')
            if not tag_b:
                continue
            titulo = tag_b.get_text(strip=True)
            titulo_pai = tag_b.find_parent('div', class_='cita-artigos')
            if "Trabalhos completos" in titulo:
                self.data['trabalhos_completos'] = self.extract_generic_productions(titulo_pai)
            elif "Resumos expandidos" in titulo:
                self.data['resumos_expandidos'] = self.extract_generic_productions(titulo_pai)
            elif "Resumos publicados" in titulo: 
                self.data['resumos_publicados'] = self.extract_generic_productions(titulo_pai)

    def extract_orientations(self):
        try:
            tipos = [
                ('Orientacoesconcluidas', 'orientacoes_concluidas'),
                ('Orientacaoemandamento', 'orientacoes_em_andamento')
            ]
            for tag_html, chave_dic in tipos:
                lista_orientacoes = []
                anchor = self.soup.find('a', attrs={'name': tag_html})
                if anchor:
                    for sibling in anchor.find_next_siblings():
                        if sibling.name == 'a' and sibling.has_attr('name'):
                            break
                        if sibling.name == 'div' and 'layout-cell-11' in sibling.get('class', []):
                            texto = sibling.get_text(strip=True)
                            texto = self.limpar_texto(texto)
                            match = re.search(
                                r"^\s*(?P<nome>.+)\.\s+(?P<titulo>.+?)\.\s*(?:In[ií]cio:\s)?(?P<ano>\d{4})",
                                texto,
                                re.IGNORECASE | re.DOTALL
                            )
                            if match:
                                dados = {
                                    'aluno': match.group('nome').strip(),
                                    'titulo': match.group('titulo').strip(),
                                    'ano': match.group('ano').strip(),
                                }
                            else:
                                dados = {
                                    'aluno': texto, 'titulo': '', 'ano': ''
                                }
                            lista_orientacoes.append(dados)
                self.data[chave_dic] = lista_orientacoes
        except Exception as e:
            print(f"Erro ao extrair as orientações: {e}")
            self.data['orientacoes_concluidas'] = []
            self.data['orientacoes_em_andamento'] = []

    # Extrai projetos de pesquisa com descrição/resumo, situação, natureza, integrantes e anos separados.
    def extract_projects(self):
        try:
            projects_list = []
            projects_tag = self.soup.find('a', attrs={'name': 'ProjetosPesquisa'})
            if projects_tag:
                data_cell = projects_tag.find_next('div', class_='data-cell')
                if data_cell:
                    items = data_cell.find_all('div', class_='layout-cell-pad-5')
                    current_proj = None
                    for item in items:
                        text = item.get_text(separator=' ', strip=True)
                        text = self.limpar_texto(text)
                        if not text:
                            continue
                        match_periodo = re.search(r'^(\d{4})\s*-\s*(\d{4}|Atual)\b', text, re.IGNORECASE)
                        if match_periodo:
                            if current_proj:
                                projects_list.append(current_proj)
                            ano_ini = int(match_periodo.group(1))
                            ano_f_str = match_periodo.group(2).strip()
                            ano_f = "Atual" if ano_f_str.lower() == 'atual' else int(ano_f_str)
                            periodo = f"{ano_ini} - {ano_f}"
                            resto = text[match_periodo.end():].strip(" .:-")
                            current_proj = {
                                'periodo': periodo,
                                'ano_inicio': ano_ini,
                                'ano_fim': ano_f,
                                'titulo': resto if len(resto) > 2 else "",
                                'descricao': "",
                                'situacao': "",
                                'natureza': "",
                                'integrantes': []
                            }
                        elif current_proj:
                            if not current_proj['titulo'] and not any(text.startswith(k) for k in ["Descrição:", "Descri", "Situação:", "Situa"]):
                                current_proj['titulo'] = text.strip(" .")
                            else:
                                if "Descrição:" in text or "Descri" in text:
                                    m_desc = re.search(r'Descri[çc][ãa]o:\s*(.*?)(?=(?:Situa[çc][ãa]o:|Alunos envolvidos:|Integrantes:|Financiador|$))', text, re.DOTALL)
                                    if m_desc:
                                        current_proj['descricao'] = m_desc.group(1).strip(" .")
                                    else:
                                        current_proj['descricao'] = text.strip()
                                    m_sit = re.search(r'Situa[çc][ãa]o:\s*([^;.]+)', text)
                                    if m_sit:
                                        current_proj['situacao'] = m_sit.group(1).strip()
                                    m_nat = re.search(r'Natureza:\s*([^;.]+)', text)
                                    if m_nat:
                                        current_proj['natureza'] = m_nat.group(1).strip()
                                    m_integ = re.search(r'Integrantes:\s*(.*?)(?=(?:Financiador|$))', text, re.DOTALL)
                                    if m_integ:
                                        integ_str = m_integ.group(1).strip(" .")
                                        integrantes = []
                                        for part in integ_str.split('/'):
                                            part = part.strip()
                                            if '-' in part:
                                                n, r = part.rsplit('-', 1)
                                                integrantes.append({'nome': n.strip(), 'papel': r.strip()})
                                            elif part:
                                                integrantes.append({'nome': part.strip(), 'papel': ''})
                                        current_proj['integrantes'] = integrantes
                    if current_proj:
                        projects_list.append(current_proj)
                    self.data['projetos'] = projects_list
            else:
                self.data['projetos'] = []
        except Exception as e:
            print(f"Erro ao extrair os projetos: {e}")
            self.data['projetos'] = []

    # Extrai linhas de pesquisa.
    def extract_research_lines(self):
        linhas_pesquisa = []
        try:
            ancora_linhas = self.soup.find('a', {'name': 'LinhaPesquisa'})
            if ancora_linhas:
                container_secao = ancora_linhas.find_parent('div', class_='title-wrapper')
                data_cell = container_secao.find('div', class_='data-cell') if container_secao else None
                celulas_pesquisa = data_cell.find_all('div', class_='layout-cell-9') if data_cell else []
                for celula in celulas_pesquisa:
                    texto_bruto = celula.get_text(separator=' ', strip=True)
                    texto_limpo = self.limpar_texto(texto_bruto)
                    if texto_limpo and texto_limpo not in linhas_pesquisa:
                        linhas_pesquisa.append(texto_limpo)
        except Exception as e:
            print(f"Não foi possível extrair linhas de pesquisa. Erro: {e}")
        self.data['linhas_pesquisa'] = linhas_pesquisa

    # Método principal que orquestra todas as extrações.
    def parse(self):
        print("Iniciando análise do Lattes...")
        self.extract_lattes_id()
        self.extract_name()
        self.extract_citation_names()
        self.extract_address()
        self.extract_historical_addresses()
        self.extract_activity()
        self.extract_articles()
        self.extract_productions()
        self.extract_orientations()
        self.extract_projects()
        self.extract_research_lines()
        print("Análise concluída.")
        return self.data


if __name__ == "__main__":
    
    # Obtém a lista de IDs a partir dos arquivos presentes em curriculos/
    caminho_curriculos = 'curriculos'
    if os.path.exists(caminho_curriculos):
        lista_ids = sorted([f for f in os.listdir(caminho_curriculos) if os.path.isfile(os.path.join(caminho_curriculos, f)) and not f.startswith('.')])
    else:
        lista_ids = [
            "9826346918182685",
            "4706525645223041",
            "5212303626376503",
            "0038936541518854",
            "9754332336954137",
            "5119417295487126",
            "6923877786371495",
            "6743301470746932",
            "6847311664433673",
            "9403804691367376",
            "3532058764024942",
            "5321313558714462",
            "4579286987089372",
            "1957942090126269",
            "8498467320034486",
            "9933650905615452",
            "0461451015026948",
            "1624091546521389",
            "9542083518570573",
            "6881990637613409",
            "8251270609012225",
            "0391758954520783",
            "3486202914688351",
            "8516223928904348",
            "7020467292690112",
            "5333709865535244",
            "5236549058240153",
            "4990968421738051",
            "5444380855577045",
            "0422652925722673",
            "4746829076971556",
            "7287108960864123",
            "0677617028146410",
            "1705430650855494",
            "2896049826673626",
            "1413071683140519",
            "5839043594908917",
            "2870655742911951",
            "6652079760634274",
            "5449448657729439",
            "7670383899259509",
            "0769819544839146",
            "0309287112277751",
            "7570230588831120",
            "5185829124608696",
            "8528111459865939",
            "0920196032137472",
            "9170893104155674",
            "9632409046763256",
            "6446047463034654",
            "3687551763124327",
            "7952918513827867",
            "0616238673458322",
            "0987355219242506"
        ]
        
    pasta_saida = 'curriculos_json'
    os.makedirs(pasta_saida, exist_ok=True)
    
    print(f"Iniciando processamento de {len(lista_ids)} currículos...")
    for id_lattes in lista_ids:
        html_file_path = os.path.join(caminho_curriculos, id_lattes)

        try:
            with open(html_file_path, 'r', encoding='utf-8') as fp:
                html_content = fp.read()
            
            lattes_parser = LattesParser(html_content)
            dados_do_curriculo = lattes_parser.parse()
            
            nome_arquivo = dados_do_curriculo.get('nome_completo') or id_lattes
            caminho_json = os.path.join(pasta_saida, f"{nome_arquivo}.json")
            
            with open(caminho_json, 'w', encoding='utf-8') as json_file:
                json.dump(dados_do_curriculo, json_file, indent=4, ensure_ascii=False)
            
            print(f"Sucesso: {nome_arquivo} ({id_lattes}) -> {caminho_json}")

        except FileNotFoundError:
            print(f"Erro: Arquivo '{html_file_path}' não encontrado.")
        except Exception as e:
            print(f"Um erro inesperado ocorreu em {id_lattes}: {e}")