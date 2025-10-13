import requests
from bs4 import BeautifulSoup
import pandas as pd 
from itertools import zip_longest  #Alinhar listas em linhas

# Princípio 'SOLID' aplicado (estudado em vídeo para aplicação prática):
# 'S'RP: a função scrape_site só faz scraping dado um contrato; SiteConfig só descreve cada site.
# 'O'CP: usado para adicionar um novo site, criando uma nova configuração (sem mudar a lógica).
# 'L'SP: qualquer config "se comporta" como site válido para a função genérica.
# 'I'SP: só definimos o necessário (url, contêiner e seletores).
# 'D'IP: a lógica depende da abstração SiteConfig, não de sites concretos.
# 'D'RY: o extract_text_list/extract_links_list evita a repetição de código.

class SiteConfig:
    def __init__(self, url, container_tag, container_attrs, selectors):
        """
        selectors = {
            'title':   ('tag', {'class': '...'}),
            'summary': ('tag', {'class': '...'}),
            'date':    ('tag', {'class': '...'}),  
            'link':    ('tag', {'...': '...'})     
        }
        """
        self.url = url
        self.container_tag = container_tag
        self.container_attrs = container_attrs
        self.selectors = selectors

def extract_text_list(parent, tag, attrs):
    return [el.get_text(strip=True) for el in parent.find_all(tag, attrs=attrs)]

def extract_links_list(parent, tag, attrs):
    return [el.get('href', '').strip() for el in parent.find_all(tag, attrs=attrs)]

_rows_all = []

def scrape_site(config: SiteConfig, print_label: str):
    response = requests.get(config.url)
    soup = BeautifulSoup(response.content, 'html.parser')
    containers = soup.find_all(config.container_tag, attrs=config.container_attrs)

    for cont in containers:
        titles_list   = extract_text_list(cont, *config.selectors['title'])
        summaries_list= extract_text_list(cont, *config.selectors['summary'])
        
        if 'date' in config.selectors and config.selectors['date'] is not None:
            dates_list = extract_text_list(cont, *config.selectors['date'])
        else:
            dates_list = []

        links_list    = extract_links_list(cont, *config.selectors['link'])

        noticia = {
            'Title': titles_list,
            'Summary': summaries_list,
            'Date': dates_list,
            'Link': links_list
        }
        print(noticia if not print_label else noticia)

        
        for t, s, d, l in zip_longest(titles_list, summaries_list, dates_list, links_list, fillvalue=''):
            _rows_all.append({'Title': t, 'Summary': s, 'Date': d, 'Link': l})

# Configurações dos 4 sites de notícias

# 1) ANATEL
anatel_cfg = SiteConfig(
    url="https://www.gov.br/anatel/pt-br/assuntos/noticias",
    container_tag="ul",
    container_attrs={'class': 'noticias listagem-noticias-com-foto'},
    selectors={
        'title':   ('h2',  {'class': 'titulo'}),
        'summary': ('p',   {'class': 'descricao'}),
        'date':    ('span',{'class': 'data'}),
        'link':    ('a',   {})
    }
)

# 2) ANAC
anac_cfg = SiteConfig(
    url="https://www.gov.br/anac/pt-br/noticias/ultimas-noticias-1",
    container_tag="div",
    container_attrs={'id': 'content-core'},
    selectors={
        'title':   ('h2',  {'class': 'tileHeadline'}),
        'summary': ('span',{'class': 'description'}),
        'date':    ('span',{'class': 'summary-view-icon'}),
        'link':    ('a',   {})
    }
)

# 3) ANEEL
aneel_cfg = SiteConfig(
    url="https://www.gov.br/aneel/pt-br/assuntos/noticias",
    container_tag="ul",
    container_attrs={'class': 'noticias listagem-noticias-com-foto'},
    selectors={
        'title':   ('h2',  {'class': 'titulo'}),
        'summary': ('span',{'class': 'descricao'}),
        'date':    ('span',{'class': 'data'}),
        'link':    ('a',   {})
    }
)

# 4) ANVISA
anvisa_cfg = SiteConfig(
    url="https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa",
    container_tag="ul",
    container_attrs={'class': 'noticias listagem-noticias-com-foto'},
    selectors={
        'title':   ('h2',  {'class': 'titulo'}),
        'summary': ('span',{'class': 'descricao'}),
        'date':    ('span',{'class': 'data'}),  
        'link':    ('a',   {})
    }
)

scrape_site(anatel_cfg, print_label="noticia1")
scrape_site(anac_cfg,   print_label="noticia2")
scrape_site(aneel_cfg,  print_label="noticia3")
scrape_site(anvisa_cfg, print_label="noticia4")

df = pd.DataFrame(_rows_all, columns=['Title', 'Summary', 'Date', 'Link'])
df.to_excel('noticias.xlsx', index=False)
print(f'Salvo: noticias.xlsx | linhas: {len(df)}')
