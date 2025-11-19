from collections import defaultdict
from bs4 import BeautifulSoup
import re

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

            if not articles_tags:
                raise ValueError("Rótulo 'informacao artigo' não encontrado.")
            
            for artigo in articles_tags:
                artigo_tag = artigo.find('div', class_='layout-cell-11')
                doi_tag = artigo_tag.find('div', class_='icone-doi')
                link_doi = doi_tag['href']
                titulo_artigo = artigo_tag.get_text(strip = True)
                print(link_doi)
                print(titulo_artigo)
                
        except Exception as e:
            print(f"Erro ao extrair artigos publicados: {e}")
            self.data['artigos'] = None
        
    # Método principal que orquestra todas as extrações.
    def parse(self):
       
        print("Iniciando análise do Lattes...")
        self.extract_name()
        self.extract_lattes_id()
        self.extract_address()
        self.extract_activity()
        self.extract_articles()
        
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

    except FileNotFoundError:
        print(f"Erro: Arquivo '{html_file_path}' não encontrado.")
    except Exception as e:
        print(f"Um erro inesperado ocorreu: {e}")