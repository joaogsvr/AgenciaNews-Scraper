# Importa a função para estabelecer a conexão com o banco de dados
from db_connection import get_db_connection
import psycopg

# Função para criar a tabela de notícias
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
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_create_table)
            conn.commit()
            
    print("Tabela 'noticias' verificada/criada com sucesso.")

# Função para inserir múltiplas notícias de uma só vez
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
            # executemany é a forma otimizada para inserção em lote no psycopg.
            cur.executemany(sql_insert, news_list)
            cur.execute("SELECT rowcount FROM pg_stat_activity WHERE pid = pg_backend_pid()")
            inserted_count = cur.fetchone()[0] # Captura o número real de linhas inseridas
            conn.commit()
            
        print(f"Inserção em lote concluída: {inserted_count} itens inseridos (ou atualizados, se aplicável).")
        
    except Exception as e:
        print(f"ERRO na inserção em lote: {e}")
        if conn:
            # Rollback em caso de erro para garantir a integridade.
            conn.rollback() 
    finally:
        # Garante que a conexão seja fechada.
        if conn:
            conn.close()