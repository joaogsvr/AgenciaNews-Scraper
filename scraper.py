# =========================================================================================
# SCRAPER DE NOTÍCIAS DE AGÊNCIAS REGULADORAS BRASILEIRAS
# =========================================================================================
#
# OBJETIVO: Coletar (scrape) automaticamente as notícias das páginas oficiais 
# das seguintes Agências Reguladoras Federais:
#
# - ANATEL (Agência Nacional de Telecomunicações)
# - ANAC (Agência Nacional de Aviação Civil)
# - ANEEL (Agência Nacional de Energia Elétrica)
# - ANVISA (Agência Nacional de Vigilância Sanitária)
#
# O script navega nos respectivos URLs, extrai Título, Resumo, Data e Link
# de cada notícia e salva os dados coletados em um banco de dados PostgreSQL.
# Para evitar bloqueios e ser um "bom vizinho", são utilizados User-Agents
# e pausas (delays) entre as requisições a cada site.
#
# =========================================================================================

# Importa a biblioteca para fazer requisições HTTP (acessar websites)
import requests
# Importa a biblioteca para fazer o parse (análise) do HTML
from bs4 import BeautifulSoup
# Importa o módulo 'time' para adicionar pausas (delays) entre as requisições
import time 
# Importa funções para interagir com o banco de dados (assumindo que 'db_utils' existe)
from db_utils import create_news_table, bulk_insert_news 

# Define a estrutura de configuração para cada site de notícias
class SiteConfig:
    # Construtor da classe, recebe os parâmetros de configuração
    def __init__(self, url, container_selector, item_selector, selectors, post_processor_func=None):
        # URL base do site a ser raspado
        self.url = url
        # Seletor CSS do elemento HTML que contém a lista de notícias (o "bloco" maior)
        self.container_selector = container_selector 
        # Seletor CSS do elemento HTML que representa uma única notícia
        self.item_selector = item_selector        
        # Dicionário contendo os seletores específicos para Título, Resumo, Data e Link
        self.selectors = selectors
        # Função opcional para processar (limpar) os dados após a coleta
        self.post_processor_func = post_processor_func

# Função auxiliar para extrair o texto de um elemento HTML
def find_text(parent, tag, attrs):
    # Procura o elemento dentro do elemento 'parent'
    el = parent.find(tag, attrs=attrs)
    # Retorna o texto limpo (sem espaços extras) se o elemento for encontrado, senão retorna string vazia
    return el.get_text(strip=True) if el else ''

# Função auxiliar para extrair o link (atributo 'href') de um elemento HTML
def find_link(parent, tag, attrs):
    # Procura o elemento dentro do elemento 'parent'
    el = parent.find(tag, attrs=attrs)
    # Retorna o valor do atributo 'href' limpo se o elemento for encontrado, senão retorna string vazia
    return el.get('href', '').strip() if el else ''

# Função de pós-processamento para remover datas duplicadas do início dos resumos
def clean_data(titles, summaries, dates, links):
    cleaned_summaries = []
    # Itera sobre as listas de data e resumo em paralelo
    for date, summary in zip(dates, summaries):
        # Verifica se o resumo existe, a data existe e o resumo começa com a string da data
        if summary and date and summary.startswith(date):
            # Remove a data do início do resumo
            cleaned_summary = summary[len(date):]
            # Remove o traço e espaços do início da string limpa
            cleaned_summary = cleaned_summary.lstrip('-').strip()
            cleaned_summaries.append(cleaned_summary)
        else:
            # Se não houver data duplicada, usa o resumo original
            cleaned_summaries.append(summary)
    # Retorna todas as listas, mas com os resumos potencialmente corrigidos
    return titles, cleaned_summaries, dates, links

# Função principal que executa o scraping em um site específico
def scrape_site(config: SiteConfig, print_label: str, headers: dict):
    # Imprime mensagem de início para rastreamento
    print(f"Iniciando scraping de: {print_label} ({config.url})")
    try:
        # Faz a requisição HTTP GET para a URL, incluindo os cabeçalhos (headers)
        response = requests.get(config.url, headers=headers) 
        # Levanta um erro se a requisição retornar um status de erro (ex: 404, 500)
        response.raise_for_status() 
    except requests.RequestException as e:
        # Imprime o erro e retorna uma lista vazia de notícias em caso de falha na requisição
        print(f"ERRO ao buscar {print_label}: {e}")
        return [] 

    # Cria o objeto BeautifulSoup para analisar o conteúdo HTML da resposta
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Busca todos os elementos que correspondem ao seletor do container principal
    containers = soup.select(config.container_selector)
    # Se nenhum container for encontrado, emite um aviso e interrompe
    if not containers:
        print(f"AVISO: Nenhum container encontrado para {print_label}. O seletor '{config.container_selector}' pode estar errado ou a página foi bloqueada.")
        return []

    
    found_news = []
    
    # Itera sobre cada container encontrado
    for cont in containers:
        # Dentro do container, busca todos os elementos que representam uma única notícia
        items = cont.select(config.item_selector)
        # Se nenhum item (notícia) for encontrado dentro do container, emite um aviso
        if not items:
             print(f"AVISO: Nenhum item encontrado para {print_label} dentro do container. O seletor de item '{config.item_selector}' pode estar errado.")
        
        # Itera sobre cada item (notícia) encontrado
        for item in items:
            # Extrai o título usando a função find_text e o seletor configurado
            t = find_text(item, *config.selectors['title'])
            # Extrai o resumo usando a função find_text e o seletor configurado
            s = find_text(item, *config.selectors['summary'])
            
            d = ''
            # Verifica se o seletor de data foi fornecido na configuração
            if 'date' in config.selectors and config.selectors['date'] is not None:
                # Extrai a data
                d = find_text(item, *config.selectors['date'])
            
            # Extrai o link usando a função find_link e o seletor configurado
            l = find_link(item, *config.selectors['link'])
            
            # Bloco de lógica para tentar encontrar o link caso o seletor 'link' não funcione
            if not l and t:
                # Tenta encontrar o elemento do título
                title_link_el = item.find(config.selectors['title'][0], config.selectors['title'][1])
                if title_link_el:
                    # Se o próprio elemento do título for um <a> (link), extrai o 'href'
                    if title_link_el.name == 'a':
                         l = title_link_el.get('href', '').strip()
                    else: 
                        # Caso contrário, procura um <a> dentro do elemento do título
                         l_el_inside = title_link_el.find('a')
                         if l_el_inside:
                            l = l_el_inside.get('href', '').strip()

            # Aplica a função de pós-processamento (se configurada) para limpar os dados
            if config.post_processor_func:
                try:
                    # Aplica a função (ela espera listas, por isso as tuplas com item único)
                    (t,), (s,), (d,), (l,) = config.post_processor_func([t], [s], [d], [l])
                except Exception as e:
                    # Imprime um erro se o pós-processamento falhar, mas continua
                    print(f"Erro no post_processor_func para {print_label}: {e}")
                    pass 

            # Adiciona os dados coletados (título, resumo, data, link) à lista de notícias
            found_news.append((t, s, d, l))
    
    # Imprime o resumo da coleta
    print(f"Scraping de {print_label} concluído. {len(found_news)} itens encontrados.")
    # Retorna a lista de notícias
    return found_news
    
# --- Configurações Específicas dos Sites ---

# 1) ANATEL (Agência Nacional de Telecomunicações)
anatel_cfg = SiteConfig(
    url="https://www.gov.br/anatel/pt-br/assuntos/noticias",
    container_selector="ul.noticias.listagem-noticias-com-foto", 
    item_selector="li", 
    selectors={
        'title':   ('h2',   {'class': 'titulo'}),
        'summary': ('span', {'class': 'descricao'}), 
        'date':    ('span', {'class': 'data'}),      
        'link':    ('a',    {}) 
    },
    # Usa a função 'clean_data' para este site
    post_processor_func=clean_data
)

# 2) ANAC (Agência Nacional de Aviação Civil)
anac_cfg = SiteConfig(
    url="https://www.gov.br/anac/pt-br/noticias/ultimas-noticias-1",
    container_selector="div#content-core",  
    item_selector="article.tileItem",      
    selectors={
        'title':   ('h2',   {'class': 'tileHeadline'}),
        'summary': ('span', {'class': 'description'}),
        'date':    ('span', {'class': 'summary-view-icon'}),
        'link':    ('a',    {'class': 'summary'})
    }
    # Não precisa de post_processor_func
)

# 3) ANEEL (Agência Nacional de Energia Elétrica)
aneel_cfg = SiteConfig(
    url="https://www.gov.br/aneel/pt-br/assuntos/noticias",
    container_selector="ul.noticias.listagem-noticias-com-foto", 
    item_selector="li", 
    selectors={
        'title':   ('h2',   {'class': 'titulo'}),
        'summary': ('span', {'class': 'descricao'}),
        'date':    ('span', {'class': 'data'}),
        'link':    ('a',    {})
    },
    # Usa a função 'clean_data' para este site
    post_processor_func=clean_data
)


# 4) ANVISA (Agência Nacional de Vigilância Sanitária)
anvisa_cfg = SiteConfig(
    url="https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa",
    container_selector="ul.noticias.listagem-noticias-com-foto", 
    item_selector="li", 
    selectors={
        'title':   ('h2',   {'class': 'titulo'}),
        'summary': ('span', {'class': 'descricao'}),
        'date':    ('span', {'class': 'data'}),  
        'link':    ('a',    {})
    },
    # Usa a função 'clean_data' para este site
    post_processor_func=clean_data
)


# --- Bloco Principal de Execução ---

# Este bloco só é executado quando o script é chamado diretamente (e não importado)
if __name__ == "__main__":
    
    # Define um dicionário com cabeçalhos HTTP para simular um navegador comum (User-Agent)
    # Isso ajuda a evitar bloqueios por parte do servidor do site
    HTTP_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    }
    
    # Define o tempo de espera em segundos entre o scraping de um site e o próximo
    DELAY_ENTRE_SITES = 3 # 3 segundos

    # Chama a função para garantir que a tabela de notícias exista no banco de dados
    print("Verificando/Criando tabela no banco de dados...")
    create_news_table()
    
    # Lista que armazenará todas as notícias coletadas de todos os sites
    all_news_list = []
    
    # 1. Scraping da ANATEL
    # Executa o scraping e adiciona os resultados à lista principal
    all_news_list.extend(scrape_site(anatel_cfg, print_label="ANATEL", headers=HTTP_HEADERS))
    # Pausa para evitar sobrecarregar o servidor
    print(f"--- Pausando por {DELAY_ENTRE_SITES} segundos ---")
    time.sleep(DELAY_ENTRE_SITES) 

    # 2. Scraping da ANAC
    all_news_list.extend(scrape_site(anac_cfg, print_label="ANAC", headers=HTTP_HEADERS))
    # Pausa
    print(f"--- Pausando por {DELAY_ENTRE_SITES} segundos ---")
    time.sleep(DELAY_ENTRE_SITES) 

    # 3. Scraping da ANEEL
    all_news_list.extend(scrape_site(aneel_cfg, print_label="ANEEL", headers=HTTP_HEADERS))
    # Pausa
    print(f"--- Pausando por {DELAY_ENTRE_SITES} segundos ---")
    time.sleep(DELAY_ENTRE_SITES) 

    # 4. Scraping da ANVISA (último site, não precisa de pausa depois)
    all_news_list.extend(scrape_site(anvisa_cfg, print_label="ANVISA", headers=HTTP_HEADERS))
    
    # Imprime o total geral de itens coletados
    print(f"\nScraping finalizado. Total de {len(all_news_list)} itens coletados de todos os sites.")

    # Filtra a lista, mantendo apenas os itens que possuem um link válido (campo 3 da tupla)
    valid_news = [item for item in all_news_list if item[3] and item[3].strip()]
    
    # Imprime o número de itens que serão salvos
    print(f"Filtragem concluída. {len(valid_news)} itens válidos (com link) serão inseridos.")

    # Chama a função para inserir em lote (bulk insert) os dados válidos no banco de dados
    bulk_insert_news(valid_news)
    
    # Imprime a mensagem de conclusão
    print("\nProcesso concluído! Dados salvos no banco de dados PostgreSQL.")