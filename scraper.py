import requests
from bs4 import BeautifulSoup
import time 
# Assume-se que 'db_utils' lida com a conexão e inserção no PostgreSQL
from database import create_news_table, bulk_insert_news 

# --- Classes e Configurações ---

class SiteConfig:
    """Estrutura de configuração para um site de notícias específico."""
    def __init__(self, url, container_selector, item_selector, selectors, post_processor_func=None):
        self.url = url
        self.container_selector = container_selector 
        self.item_selector = item_selector        
        self.selectors = selectors
        self.post_processor_func = post_processor_func

# --- Funções Auxiliares de Extração ---

def find_text(parent, tag, attrs):
    """Extrai o texto de um elemento HTML. Retorna string vazia se não for encontrado."""
    el = parent.find(tag, attrs=attrs)
    return el.get_text(strip=True) if el else ''

def find_link(parent, tag, attrs):
    """Extrai o atributo 'href' de um elemento HTML. Retorna string vazia se não for encontrado."""
    el = parent.find(tag, attrs=attrs)
    return el.get('href', '').strip() if el else ''

def clean_data(titles, summaries, dates, links):
    """
    Função de pós-processamento para sites .gov.br.
    Remove a data duplicada que alguns sites inserem no início do resumo.
    """
    cleaned_summaries = []
    for date, summary in zip(dates, summaries):
        # Verifica se o resumo começa com a data e remove se for o caso.
        if summary and date and summary.startswith(date):
            cleaned_summary = summary[len(date):].lstrip('-').strip()
            cleaned_summaries.append(cleaned_summary)
        else:
            cleaned_summaries.append(summary)
    return titles, cleaned_summaries, dates, links

# --- Função Principal de Scraping ---

def scrape_site(config: SiteConfig, print_label: str, headers: dict):
    """Executa o scraping em um site específico com base na configuração fornecida."""
    print(f"Iniciando scraping de: {print_label} ({config.url})")
    try:
        response = requests.get(config.url, headers=headers) 
        response.raise_for_status() 
    except requests.RequestException as e:
        print(f"ERRO ao buscar {print_label}: {e}")
        return [] 

    soup = BeautifulSoup(response.content, 'html.parser')
    containers = soup.select(config.container_selector)
    
    if not containers:
        # Mantive o aviso, pois falhas de seletor são um "porquê" importante.
        print(f"AVISO: Nenhum container encontrado. O seletor '{config.container_selector}' pode estar errado.")
        return []

    found_news = []
    
    for cont in containers:
        items = cont.select(config.item_selector)
        
        if not items:
              print(f"AVISO: Nenhum item encontrado dentro do container.")
        
        for item in items:
            t = find_text(item, *config.selectors['title'])
            s = find_text(item, *config.selectors['summary'])
            
            d = ''
            if 'date' in config.selectors and config.selectors['date'] is not None:
                d = find_text(item, *config.selectors['date'])
            
            l = find_link(item, *config.selectors['link'])
            
            # Lógica de fallback para encontrar o link se o seletor inicial falhar.
            if not l and t:
                title_link_el = item.find(config.selectors['title'][0], config.selectors['title'][1])
                if title_link_el:
                    if title_link_el.name == 'a':
                         l = title_link_el.get('href', '').strip()
                    else: 
                         l_el_inside = title_link_el.find('a')
                         if l_el_inside:
                            l = l_el_inside.get('href', '').strip()

            if config.post_processor_func:
                try:
                    # Aplica a função em tuplas de item único para desempacotamento seguro.
                    (t,), (s,), (d,), (l,) = config.post_processor_func([t], [s], [d], [l])
                except Exception as e:
                    print(f"Erro no post_processor_func para {print_label}: {e}")
                    pass 

            found_news.append((t, s, d, l))
    
    print(f"Scraping de {print_label} concluído. {len(found_news)} itens encontrados.")
    return found_news
    
# --- Configurações Específicas dos Sites ---
# As configurações são concisas e autodocumentáveis pelo nome das chaves.

# 1) ANATEL
anatel_cfg = SiteConfig(
    url="https://www.gov.br/anatel/pt-br/assuntos/noticias",
    container_selector="ul.noticias.listagem-noticias-com-foto", 
    item_selector="li", 
    selectors={
        'title':   ('h2',   {'class': 'titulo'}),
        'summary': ('span', {'class': 'descricao'}), 
        'date':    ('span', {'class': 'data'}),      
        'link':    ('a',    {}) 
    },
    post_processor_func=clean_data
)

# 2) ANAC
anac_cfg = SiteConfig(
    url="https://www.gov.br/anac/pt-br/noticias/ultimas-noticias-1",
    container_selector="div#content-core",  
    item_selector="article.tileItem",      
    selectors={
        'title':   ('h2',   {'class': 'tileHeadline'}),
        'summary': ('span', {'class': 'description'}),
        'date':    ('span', {'class': 'summary-view-icon'}),
        'link':    ('a',    {'class': 'summary'})
    }
)

# 3) ANEEL
aneel_cfg = SiteConfig(
    url="https://www.gov.br/aneel/pt-br/assuntos/noticias",
    container_selector="ul.noticias.listagem-noticias-com-foto", 
    item_selector="li", 
    selectors={
        'title':   ('h2',   {'class': 'titulo'}),
        'summary': ('span', {'class': 'descricao'}),
        'date':    ('span', {'class': 'data'}),
        'link':    ('a',    {})
    },
    post_processor_func=clean_data
)

# 4) ANVISA
anvisa_cfg = SiteConfig(
    url="https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa",
    container_selector="ul.noticias.listagem-noticias-com-foto", 
    item_selector="li", 
    selectors={
        'title':   ('h2',   {'class': 'titulo'}),
        'summary': ('span', {'class': 'descricao'}),
        'date':    ('span', {'class': 'data'}),  
        'link':    ('a',    {})
    },
    post_processor_func=clean_data
)

# --- Bloco Principal de Execução ---

if __name__ == "__main__":
    
    # User-Agent para simular um navegador comum e evitar bloqueios do servidor.
    HTTP_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    }
    
    # Delay em segundos para ser um "bom vizinho" e evitar sobrecarregar/bloquear o servidor.
    DELAY_ENTRE_SITES = 3 

    print("Verificando/Criando tabela no banco de dados...")
    create_news_table()
    
    all_news_list = []
    
    # Execução sequencial com delay
    
    all_news_list.extend(scrape_site(anatel_cfg, print_label="ANATEL", headers=HTTP_HEADERS))
    print(f"--- Pausando por {DELAY_ENTRE_SITES} segundos ---")
    time.sleep(DELAY_ENTRE_SITES) 

    all_news_list.extend(scrape_site(anac_cfg, print_label="ANAC", headers=HTTP_HEADERS))
    print(f"--- Pausando por {DELAY_ENTRE_SITES} segundos ---")
    time.sleep(DELAY_ENTRE_SITES) 

    all_news_list.extend(scrape_site(aneel_cfg, print_label="ANEEL", headers=HTTP_HEADERS))
    print(f"--- Pausando por {DELAY_ENTRE_SITES} segundos ---")
    time.sleep(DELAY_ENTRE_SITES) 

    # Último site, sem necessidade de pausa subsequente.
    all_news_list.extend(scrape_site(anvisa_cfg, print_label="ANVISA", headers=HTTP_HEADERS))
    
    print(f"\nScraping finalizado. Total de {len(all_news_list)} itens coletados.")

    # Filtra notícias sem link válido antes da inserção.
    valid_news = [item for item in all_news_list if item[3] and item[3].strip()]
    
    print(f"Filtragem concluída. {len(valid_news)} itens válidos serão inseridos.")

    bulk_insert_news(valid_news)
    
    print("\nProcesso concluído! Dados salvos no banco de dados PostgreSQL.")