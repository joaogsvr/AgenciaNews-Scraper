# scraper.py
import requests
from bs4 import BeautifulSoup
import time 

# Importa todas as configurações do módulo dedicado
from config import HTTP_HEADERS, DELAY_ENTRE_SITES, SCRAPER_CONFIGS, SiteConfig

# Importa as utilidades do banco de dados (que já estão unidas)
from database import create_news_table, bulk_insert_news

# --- Funções Auxiliares de Extração ---

def find_text(parent, tag, attrs):
    """Extrai o texto de um elemento HTML. Retorna string vazia se não for encontrado."""
    el = parent.find(tag, attrs=attrs)
    return el.get_text(strip=True) if el else ''

def find_link(parent, tag, attrs):
    """Extrai o atributo 'href' de um elemento HTML. Retorna string vazia se não for encontrado."""
    el = parent.find(tag, attrs=attrs)
    return el.get('href', '').strip() if el else ''

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
                    # Aplica a função de limpeza definida no config.py
                    (t,), (s,), (d,), (l,) = config.post_processor_func([t], [s], [d], [l])
                except Exception as e:
                    print(f"Erro no post_processor_func para {print_label}: {e}")
                    pass 

            found_news.append((t, s, d, l))
    
    print(f"Scraping de {print_label} concluído. {len(found_news)} itens encontrados.")
    return found_news

# --- Bloco Principal de Execução ---

if __name__ == "__main__":
    
    print("Verificando/Criando tabela no banco de dados...")
    create_news_table()
    
    all_news_list = []
    
    for config, label in SCRAPER_CONFIGS:
        
        all_news_list.extend(scrape_site(config, print_label=label, headers=HTTP_HEADERS))
        
        # Pausa apenas se não for o último site da lista.
        if config != SCRAPER_CONFIGS[-1][0]:
            print(f"--- Pausando por {DELAY_ENTRE_SITES} segundos ---")
            time.sleep(DELAY_ENTRE_SITES) 

    print(f"\nScraping finalizado. Total de {len(all_news_list)} itens coletados.")

    valid_news = [item for item in all_news_list if item[3] and item[3].strip()]
    
    print(f"Filtragem concluída. {len(valid_news)} itens válidos serão inseridos.")

    bulk_insert_news(valid_news)
    
    print("\nProcesso concluído! Dados salvos no banco de dados PostgreSQL.")