# --- Configurações Globais ---

# Cabeçalhos HTTP para simular um navegador comum (User-Agent) e evitar bloqueios do servidor.
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
}

# Tempo de espera em segundos para ser um "bom vizinho" e não sobrecarregar os servidores.
DELAY_ENTRE_SITES = 3

# --- Estrutura de Configuração (Classe SiteConfig) ---

class SiteConfig:
    """Estrutura de configuração para um site de notícias específico."""
    def __init__(self, url, container_selector, item_selector, selectors, post_processor_func=None):
        self.url = url
        self.container_selector = container_selector 
        self.item_selector = item_selector        
        self.selectors = selectors
        self.post_processor_func = post_processor_func

# --- Funções de Pós-Processamento ---

def clean_data(titles, summaries, dates, links):
    """Remove a data duplicada que alguns sites inserem no início do resumo."""
    cleaned_summaries = []
    for date, summary in zip(dates, summaries):
        # Lógica para verificar e remover a data se ela aparecer no início do resumo.
        if summary and date and summary.startswith(date):
            cleaned_summary = summary[len(date):].lstrip('-').strip()
            cleaned_summaries.append(cleaned_summary)
        else:
            cleaned_summaries.append(summary)
    return titles, cleaned_summaries, dates, links

# --- Configurações Específicas dos Sites ---
# As variáveis usam o sufixo _CFG para clareza (Configuration).

ANATEL_CFG = SiteConfig(
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

ANAC_CFG = SiteConfig(
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

ANEEL_CFG = SiteConfig(
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

ANVISA_CFG = SiteConfig(
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

# Lista principal das configurações de todos os sites
SCRAPER_CONFIGS = [
    (ANATEL_CFG, "ANATEL"),
    (ANAC_CFG, "ANAC"),
    (ANEEL_CFG, "ANEEL"),
    (ANVISA_CFG, "ANVISA"),
]