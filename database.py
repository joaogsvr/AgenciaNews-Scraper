import psycopg
import sys
# Importa as funções para carregar variáveis do .env
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- 1. Configurações da Conexão ---
# As variáveis são lidas do ambiente do sistema (que foi carregado pelo load_dotenv())
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT") 
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# --- 2. Função de Conexão ---

def get_db_connection():
    """
    Estabelece e retorna uma nova conexão com o PostgreSQL.
    Encerra o script em caso de falha na conexão (OperationalError).
    """
    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        print("Conexão estabelecida com sucesso.")
        return conn
        
    # Tratamento de erro específico (ex: banco de dados está offline).
    except psycopg.OperationalError as e:
        print("ERRO FATAL: Não foi possível conectar ao banco de dados.")
        print(f"Detalhe: {e}")
        sys.exit(1)

# --- 3. Funções de Manipulação do DB ---

def create_news_table():
    """Garante que a tabela 'noticias' exista, criando-a se necessário."""
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS noticias (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        summary TEXT,
        date_text TEXT,
        -- Coluna UNIQUE para garantir que não haja notícias duplicadas.
        link TEXT NOT NULL UNIQUE,
        -- Timestamp de registro, valor padrão é o momento da inserção.
        scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    # Usa o gerenciador de contexto 'with' para garantir que a conexão seja fechada.
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_create_table)
            conn.commit()
            
    print("Tabela 'noticias' verificada/criada com sucesso.")

def bulk_insert_news(news_list):
    """
    Insere uma lista de notícias em lote. 
    Usa ON CONFLICT (link) DO NOTHING para ignorar duplicatas.
    """
    if not news_list:
        print("Nenhuma notícia nova para inserir.")
        return

    sql_insert = """
    INSERT INTO noticias (title, summary, date_text, link)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (link) DO NOTHING;
    """
    
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # executemany é a forma otimizada para inserção em lote.
            cur.executemany(sql_insert, news_list)
            
            # Tenta capturar o número real de linhas inseridas/modificadas.
            inserted_count = cur.rowcount
            
            conn.commit()
            
        print(f"Inserção em lote concluída: {inserted_count} itens processados.")
        
    except Exception as e:
        print(f"ERRO na inserção em lote: {e}")
        if conn:
            # Rollback em caso de erro para garantir a integridade.
            conn.rollback() 
    finally:
        # Garante que a conexão seja fechada.
        if conn:
            conn.close()