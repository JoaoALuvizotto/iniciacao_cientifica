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
                self.data['id_lattes'] = id_tag.text.strip()
            else:
                self.data['id_lattes'] = None
        except Exception as e:
            print(f"Erro ao extrair ID Lattes: {e}")
            self.data['id_lattes'] = None
    
    # Extrai o endereço profissional.
    def extract_address(self):
        try:
            endereco_tag = self.soup.find('b', string=re.compile(r'Endereço Profissional'))
            
            if not endereco_tag:
                raise ValueError("Rótulo 'Endereço Profissional' não encontrado.")

            #navagando pela árvore do endereço
            endereco_pai = endereco_tag.find_parent('div', class_='layout-cell-3')

            endereco_cell = endereco_pai.find_next_sibling('div', class_='layout-cell-9')

            endereco_bruto = endereco_cell.get_text(separator='\n', strip=True)
            
            endereco_limpo = re.sub(r'\s+', ' ', endereco_bruto)
            
            self.data['endereco'] = endereco_limpo.strip()

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
            activities = activity_pai.find_all('div', class_='layout-cell-9')
            
            # cria um dicionário de listas, para não haver substituição dos valores das chaves
            areas = defaultdict(list)
            for area in activities:
                #pegando as grande áreas, Áreas e as subáreas 
                texto_area = area.get_text(strip = True)
                palavra_chave = r'\s+/\s+Área:\s+'
                partes = re.split(palavra_chave, texto_area, maxsplit=2)
                
                #removendo as grande áreas, para termos somente as áreas e subáreas
                segunda_parte = partes[1].strip()
                #extraindo as subáreas
                palavra_chave2 = r'\s+/\s+Subárea:\s+'
                partes2 = re.split(palavra_chave2, segunda_parte)
                
                chave_area = partes2[0]
                valor_subarea = partes2[1]
                
                #Limpando a string de subárea, removendo os \t e \n e os pontos desnecessários
                valor_subarea = re.sub(r'\s+', ' ', valor_subarea)
                valor_subarea = re.sub(r'\.', ' ', valor_subarea)
                valor_subarea = valor_subarea.strip()
                
                #Adicionando ao dicionário de listas
                areas[chave_area].append(valor_subarea)
                
            
            self.data['area de atuacao'] = dict(areas)
            
        except Exception as e:
            print(f"Erro ao extrair as áreas de atuação: {e}")
            self.data['area de atuacao'] = None

    def extract_articles(self):
        try:
            articles_tags = self.soup.find_all('div', class_='artigo-completo')
            #print(articles_tags)
            
            if not articles_tags:
                raise ValueError("Rótulo 'artigo completo' não encontrado.")

            lista_artigos = []
            for artigo in articles_tags:
                artigo_tag = artigo.find('div', class_='layout-cell-11')
                doi_tag = artigo_tag.find('a', class_='icone-doi')
                if doi_tag:
                    link_doi = doi_tag['href']
                else:
                    link_doi = None
                
                # Limpando o texto do artigo
                texto_completo = artigo_tag.get_text(strip = True)
                texto_completo = re.sub(r'\s+', ' ', texto_completo)
                texto_completo = texto_completo.strip()
                
                #lista de dicionarios para armazenar no dicionario principal
                dados_artigo = {
                    'doi': link_doi,
                    'texto_completo': texto_completo
                }
                lista_artigos.append(dados_artigo)
                self.data['artigos'] = lista_artigos
                
        except Exception as e:
            print(f"Erro ao extrair artigos publicados: {e}")
            self.data['artigos'] = None
        
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
            
    
    #Ajustar para pegar somente o titulo do projeto e o período
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
                        text = re.sub(r'\s+', ' ', text) # Limpeza de espaços
                        
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
            
            
    #Fazer a separação das orientacoes concluidas
    #Fazer a extração dos projetos
        
    # Método principal que orquestra todas as extrações.
    def parse(self):
       
        print("Iniciando análise do Lattes...")
        self.extract_name()
        self.extract_lattes_id()
        self.extract_address()
        self.extract_activity()
        self.extract_articles()
        self.extract_productions()
        self.extract_orientations()
        self.extract_projects()
        
        print("Análise concluída.")
        return self.data


if __name__ == "__main__":
    html_file_path = 'sahudy.html' 

    try:
        with open(html_file_path, 'r', encoding='utf-8') as fp:
            html_content = fp.read()
        
        lattes_parser = LattesParser(html_content)
        dados_do_curriculo = lattes_parser.parse()
        
        for campo, valor in dados_do_curriculo.items(): 
            print(campo, valor)
        
        with open('curriculo.json', 'w', encoding='utf-8') as json_file:
            json.dump(dados_do_curriculo, json_file, indent=4, ensure_ascii=False)

    except FileNotFoundError:
        print(f"Erro: Arquivo '{html_file_path}' não encontrado.")
    except Exception as e:
        print(f"Um erro inesperado ocorreu: {e}")

    