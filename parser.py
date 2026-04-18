from collections import defaultdict
from bs4 import BeautifulSoup
import re
import json

class LattesParser:
    
    def __init__(self, html_content):
        
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.data = {}
        
    # Extrai o nome completo do pesquisador.
    def extract_name(self):
        try:
            nome_tag = self.soup.find('h2', class_='nome')
            
            if nome_tag:
                self.data['nome_completo'] = nome_tag.text.strip()
            else:
                self.data['nome_completo'] = None 
        except Exception as e:
            print(f"Erro ao extrair nome: {e}")
            self.data['nome_completo'] = None

    # Extrai o ID Lattes de 16 dígitos.
    def extract_lattes_id(self):
        try:
            id_tag = self.soup.find('span', style='font-weight: bold; color: #326C99;')
            
            if id_tag:
                self.data['_id'] = id_tag.text.strip()
            else:
                self.data['_id'] = None
        except Exception as e:
            print(f"Erro ao extrair ID Lattes: {e}")
            self.data['_id'] = None
    
    # Extrai o endereço profissional.
    def extract_address(self):
        try:
            endereco_tag = self.soup.find('b', string=re.compile(r'Endereço Profissional'))
            if not endereco_tag:
                self.data['endereco'] = None
                return

            endereco_pai = endereco_tag.find_parent('div', class_='layout-cell-3')
            endereco_cell = endereco_pai.find_next_sibling('div', class_='layout-cell-9')
            
            if endereco_cell:
                # Troca os <br> por vírgulas para manter o endereçamento organizado
                for br in endereco_cell.find_all('br'):
                    br.replace_with(', ')
                
                texto = endereco_cell.get_text(separator=' ', strip=True)
                # Remove o excesso de espaços e tabs do HTML original
                texto = re.sub(r'\s+', ' ', texto)
                texto = texto.replace(':,', ':').replace(', ,', ',')
                
                self.data['endereco'] = texto.strip()
            else:
                self.data['endereco'] = None

        except Exception as e:
            print(f"Erro ao extrair endereço: {e}")
            self.data['endereco'] = None
    
    def extract_activity(self):
        try:
            activity_tag = self.soup.find('h1', string=re.compile(r'Áreas de atuação'))
            
            if not activity_tag:
                raise ValueError("Rótulo 'Áreas de atuação' não encontrado.")
            
            pai_tag = activity_tag.find_parent('div', class_='title-wrapper')
            
            #pegando todas as areas e subareas
            activity_pai = pai_tag.find('div', class_='data-cell')
            # Fallback de segurança
            if not activity_pai:
                activity_pai = pai_tag
                
            activities = activity_pai.find_all('div', class_='layout-cell-9')
            
            # cria um dicionário de listas, para não haver substituição dos valores das chaves
            areas = defaultdict(list)
            for area in activities:
                #pegando as grande áreas, Áreas e as subáreas 
                texto_area = area.get_text(strip = True)
                palavra_chave = r'\s+/\s+Área:\s+'
                
                # Verifica se a palavra-chave "Área:" existe antes de tentar cortar
                if not re.search(palavra_chave, texto_area):
                    continue
                
                partes = re.split(palavra_chave, texto_area, maxsplit=2)
                
                #removendo as grande áreas, para termos somente as áreas e subáreas
                segunda_parte = partes[1].strip()
                
                #extraindo as subáreas
                palavra_chave2 = r'\s+/\s+Subárea:\s+'
                partes2 = re.split(palavra_chave2, segunda_parte)
                
                chave_area = partes2[0]
                
                # Remove o ponto final que pode sobrar na Área caso não haja subárea
                chave_area = re.sub(r'\.', '', chave_area).strip()
                
                # Verifica se a divisão encontrou uma subárea 
                if len(partes2) > 1:
                    valor_subarea = partes2[1]
                    
                    #Limpando a string de subárea, removendo os \t e \n e os pontos desnecessários
                    valor_subarea = re.sub(r'\s+', ' ', valor_subarea)
                    valor_subarea = re.sub(r'\.', ' ', valor_subarea)
                    valor_subarea = valor_subarea.strip()
                    
                    #Adicionando ao dicionário de listas (evitando duplicatas)
                    if valor_subarea not in areas[chave_area]:
                        areas[chave_area].append(valor_subarea)
                else:
                    # Se não houver subárea, apenas registra a chave da Área sem nenhum valor na lista
                    if chave_area not in areas:
                        areas[chave_area] = []
                
            self.data['area_de_atuacao'] = dict(areas)
            
        except Exception as e:
            print(f"Erro ao extrair as áreas de atuação: {e}")
            self.data['area_de_atuacao'] = None
            
    def processar_citacao_artigo(self, html_cell):
        for info in html_cell.find_all('span', class_='informacao-artigo'):
            info.decompose()
            
        for citado in html_cell.find_all('span', class_='citado'):
            citado.decompose()
            
        for img in html_cell.find_all('img'):
            img.decompose()
            
        texto_completo = html_cell.get_text(separator=' ', strip=True)
        texto_completo = re.sub(r'\s+', ' ', texto_completo)
        texto_limpo = re.sub(r'[\.,\s:-]+$', '.', texto_completo)
        
        partes = re.split(r'(?:\s\.\s|\.\.\s)', texto_limpo, maxsplit=1)
        
        colaboradores = []
        titulo_artigo = "Título não identificado"
        
        if len(partes) > 1:
            bloco_autores = partes[0].strip()
            resto = partes[1].strip()
            
            for autor in bloco_autores.split(';'):
                nome_limpo = autor.strip()
                if nome_limpo:
                    colaboradores.append({"nome": nome_limpo, "id_lattes": ""})
            
            partes_resto = re.split(r'\.\s', resto, maxsplit=1)
            if partes_resto:
                titulo_artigo = partes_resto[0].strip()
        else:
            colaboradores.append({"nome": texto_limpo, "id_lattes": ""})

        return colaboradores, titulo_artigo, texto_limpo
    
    def extract_articles(self):
        try:
            articles_tags = self.soup.find_all('div', class_='artigo-completo')
            
            if not articles_tags:
                raise ValueError("Rótulo 'artigo completo' não encontrado.")

            lista_artigos = []
            for artigo in articles_tags:
                artigo_tag = artigo.find('div', class_='layout-cell-11')
                
                if not artigo_tag:
                    continue

                doi_tag = artigo_tag.find('a', class_='icone-doi')
                link_doi = doi_tag['href'] if doi_tag else None
                
                # CORREÇÃO 1 e 2: Passamos a tag HTML inteira (artigo_tag) e recebemos as 3 variáveis
                colaboradores, titulo, texto_limpo = self.processar_citacao_artigo(artigo_tag)
                
                dados_artigo = {
                    'doi': link_doi,
                    'titulo': titulo,
                    'colaboradores': colaboradores,
                    'texto_completo': texto_limpo
                }
                    
                lista_artigos.append(dados_artigo)
            
            # Preenche a listaPB corretamente e garante que a chave 'artigos' não fique solta/nula
            self.data['listaPB'] = lista_artigos
            if 'artigos' in self.data:
                del self.data['artigos']
                
        except Exception as e:
            print(f"Erro ao extrair artigos publicados: {e}")
            self.data['listaPB'] = []
            self.data['artigos'] = None
            
    #adicionar linhas de pesquisas
    def extract_research_lines(self):
        linhas_pesquisa = []
        try:
            ancora_linhas = self.soup.find('a', {'name': 'LinhaPesquisa'})
               
            container_secao = ancora_linhas.find_parent('div', class_='title-wrapper')
                
            data_cell = container_secao.find('div', class_='data-cell')
                     
            celulas_pesquisa = data_cell.find_all('div', class_='layout-cell-9')
                        
            for celula in celulas_pesquisa:
                texto_bruto = celula.get_text(separator=' ', strip=True)
                texto_limpo = re.sub(r'\s+', ' ', texto_bruto)
                
                if texto_limpo and texto_limpo not in linhas_pesquisa:
                    linhas_pesquisa.append(texto_limpo)
                    
        except Exception as e:
            print(f"Não foi possível extrair linhas de pesquisa. Erro: {e}")
            
        self.data['linhas_pesquisa'] = linhas_pesquisa
        
    def extract_generic_productions(self, target):
        # Quando passa a tag name no argumento target
        if isinstance(target, str):
            encontrado = self.soup.find('a', attrs={'name': target})
            if not encontrado:
                print(f"Aviso: Seção '{target}' não encontrada.")
                return []
            
            producao_tag = encontrado.find_parent('b')
            producao_pai = producao_tag.find_parent('div', class_='cita-artigos')
            sibling = producao_pai.find_next_sibling('div')
        #Quando a div é passada como argumento 
        else:
            sibling = target.find_next_sibling('div')
            
        textos_producoes = []
        while sibling:
            classes_producoes = []
            classes_producoes = sibling.get('class', [])
            
            if 'cita-artigos' in classes_producoes or 'inst_back' in classes_producoes:
                break
            
            if 'layout-cell-11' in classes_producoes: 
                texto_producao = sibling.get_text(strip = True)
                texto_limpo = re.sub(r'\s+', ' ', texto_producao)
                textos_producoes.append(texto_limpo)
            
            sibling = sibling.find_next_sibling('div')
        
        
        
        return textos_producoes
    
    
    def extract_productions(self):
        
        revistas = self.extract_generic_productions('TextosJornaisRevistas') 
        self.data['producao_revistas'] = revistas
        
        todas_ancoras = self.soup.find_all('a', attrs={'name':'TrabalhosPublicadosAnaisCongresso'})
        
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
                
                # 1. Encontra a âncora
                anchor = self.soup.find('a', attrs={'name': tag_html})
                
                if anchor:
                    for sibling in anchor.find_next_siblings():
                        
                        if sibling.name == 'a' and sibling.has_attr('name'):
                            break
                        
                        if sibling.name == 'div' and 'layout-cell-11' in sibling.get('class', []):
                            texto = sibling.get_text(strip=True)
                            texto = re.sub(r'\s+', ' ', texto) # Limpa espaços
                            
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
                                # Fallback caso a regex falhe
                                dados = {
                                    'aluno': texto, 'titulo': '', 'ano': ''
                                }
                            
                            lista_orientacoes.append(dados)
                
                self.data[chave_dic] = lista_orientacoes

        except Exception as e:
            print(f"Erro ao extrair as orientações: {e}")
            self.data['orientacoes_concluidas'] = []
            self.data['orientacoes_em_andamento'] = []
            
    
    def extract_projects(self):
        try:
            projects_list = []
            projects_tag = self.soup.find('a', attrs={'name': 'ProjetosPesquisa'})
            
            if projects_tag:
                data_cell = projects_tag.find_next('div', class_='data-cell')
                
                if data_cell:
                    # Pega todos os textos do projeto
                    items = data_cell.find_all('div', class_='layout-cell-pad-5')
                    
                    current_project = None
                    
                    for item in items:
                        text = item.get_text(strip=True)
                        text = re.sub(r'\s+', ' ', text)
                        
                        # Verifica se é o ano
                        match_ano = re.search(r'^(\d{4}\s*-\s*(?:Atual|\d{4}))', text)
                        
                        if match_ano:
                            if current_project:
                                projects_list.append(current_project)
                            
                            periodo = match_ano.group(1).strip()
                            
                            resto = text[match_ano.end():].strip(" .")
                            titulo = resto if len(resto) > 2 else ""
                            
                            current_project = {
                                'periodo': periodo,
                                'titulo': titulo
                            }
                        
                        # Se não for o ano pode ser o titulo
                        elif current_project and not current_project['titulo']:
                            keywords_ignoradas = ["Descrição:", "Situação:", "Integrantes:", "Coordenador:", "Financiador(es):"]
                            
                            # Só salva se não for metadado e tiver texto suficiente
                            if len(text) > 2 and not any(k in text for k in keywords_ignoradas):
                                current_project['titulo'] = text.strip(" .")

                    # Salva o ultimo projeto
                    if current_project:
                        projects_list.append(current_project)
                    
                    self.data['projetos'] = projects_list
            else:
                print("Projetos de pesquisa não encontrados")
                self.data['projetos'] = []
           
        except Exception as e:
            print(f"Erro ao extrair os projetos: {e}")
            self.data['projetos'] = None
        
    def extract_citation_names(self):
        try:
            nomes_tag = self.soup.find('b', string=re.compile(r'Nome em citações bibliográficas'))
            if nomes_tag:
                parent_div = nomes_tag.find_parent('div', class_='layout-cell-3')
                sibling_div = parent_div.find_next_sibling('div', class_='layout-cell-9')
                nomes_brutos = sibling_div.get_text(strip=True)
                nomes_limpos = re.sub(r'\s+', ' ', nomes_brutos)
                
                # Separa os nomes por ponto e vírgula e limpa os espaços
                lista_nomes = [nome.strip() for nome in nomes_limpos.split(';') if nome.strip()]
                # Usando set para termos uma lista de elementos unicos
                self.data['listaNomesCitacao'] = sorted(list(set(lista_nomes)))
                
            else:
                self.data['listaNomesCitacao'] = []
        except Exception as e:
            print(f"Erro ao extrair nomes de citação: {e}")
            self.data['listaNomesCitacao'] = []   
    
    # Método principal que orquestra todas as extrações.
    def parse(self):
       
        print("Iniciando análise do Lattes...")
        self.extract_lattes_id()
        self.extract_name()
        self.extract_address()
        self.extract_activity()
        self.extract_articles()
        self.extract_productions()
        self.extract_orientations()
        self.extract_projects()
        self.extract_citation_names()
        self.extract_research_lines()
        
        print("Análise concluída.")
        return self.data


if __name__ == "__main__":
    
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
    for id in lista_ids:
        html_file_path = 'curriculos/' + id

        try:
            with open(html_file_path, 'r', encoding='utf-8') as fp:
                html_content = fp.read()
            
            lattes_parser = LattesParser(html_content)
            dados_do_curriculo = lattes_parser.parse()
            
            for campo, valor in dados_do_curriculo.items(): 
                print(campo, valor)
            
            with open('curriculos_json/' + dados_do_curriculo['nome_completo']+'.json', 'w', encoding='utf-8') as json_file:
                json.dump(dados_do_curriculo, json_file, indent=4, ensure_ascii=False)

        except FileNotFoundError:
            print(f"Erro: Arquivo '{html_file_path}' não encontrado.")
        except Exception as e:
            print(f"Um erro inesperado ocorreu: {e}")

    #verificar o pq q tem alguns curriculos com null na area de atuação
    #verificar se já há alguma conexão entre os curriculos
    #verificar em qual lingua está escrita as palavras para fazer o pln