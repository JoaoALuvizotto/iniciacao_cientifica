from spacy import load, displacy
from spacy.language import Language
from spacy_language_detection import LanguageDetector
import json

class plnLattes:
    def __init__(self, dados_json):
        self.dados = dados_json
        self.nlp = load('pt_core_news_sm') 

        # Função que o spaCy vai usar para criar o detector
        @Language.factory("language_detector")
        def create_language_detector(nlp, name):
            return LanguageDetector()

        # Adicionando o language_detector após o parser
        self.nlp.add_pipe('language_detector', after="parser")
        
    def transformar_curriculo_txt(self):
        texto_analise = [ 
            self.dados.get('endereco', '')
        ]
        
        areas = self.dados.get('area de atuacao', {})
        for area, especialidades in areas.items(): 
            texto_analise.append(area)
            texto_analise.extend(especialidades)
            
        artigos = self.dados.get('artigos', [])
        for artigo in artigos:
            conteudo = artigo.get('texto_completo', '')
            texto_analise.append(conteudo)
        
        producao = self.dados.get('producao_revistas', [])
        texto_analise.extend(producao)
        
        trabalhos = self.dados.get('trabalhos_completos', [])
        texto_analise.extend(trabalhos)
        
        resumos_ex = self.dados.get('resumos_expandidos', [])
        texto_analise.extend(resumos_ex)
        
        resumos_publi = self.dados.get('resumos_publicados', [])
        texto_analise.extend(resumos_publi)

        projetos = self.dados.get('projetos', [])
        
        for projeto in projetos:
            titulo = projeto.get('titulo', '')
            ano = projeto.get('periodo', '')
            
            texto_projeto = f"{titulo}; {ano}"
            
            texto_analise.append(texto_projeto)
            
        #print(texto_analise)
        #Para retonar uma string separada por espaços ao invés de uma lista
        return " ".join(texto_analise)
            
    def plnCurriculo(self, texto_curriculo):
        doc = self.nlp(texto_curriculo)
        for token in doc:
            if not token.is_stop and not token.is_punct:  
                print('{:15} | {:15} | {:15} | {:15} | {} '.format(token.text, token.pos_, token.lemma_, token.dep_, token.is_stop))
       
     
            
if __name__ == "__main__":
    
    with open('Sahudy.json', 'r', encoding='utf-8') as json_file:
        curriculo = json.load(json_file)
    
    pln = plnLattes(curriculo)
    print(pln.nlp.pipe_names)
    texto_curriculo = pln.transformar_curriculo_txt()
    #pln.plnCurriculo(texto_curriculo)
    
    