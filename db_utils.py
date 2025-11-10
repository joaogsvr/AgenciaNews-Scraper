# Importa a função para estabelecer a conexão com o banco de dados
from db_connection import get_db_connection
# Importa o driver assíncrono do PostgreSQL para Python
import psycopg

# Função para criar a tabela de notícias no banco de dados
def create_news_table():
    # Definição da consulta SQL para criar a tabela 'noticias'
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS noticias (
        -- Coluna de ID, chave primária e autoincrementável
        id SERIAL PRIMARY KEY,
        -- Título da notícia (não pode ser nulo)
        title TEXT NOT NULL,
        -- Resumo ou descrição da notícia (pode ser nulo)
        summary TEXT,
        -- Texto da data extraído (armazenado como texto)
        date_text TEXT,
        -- Link completo da notícia (não pode ser nulo e deve ser único para evitar duplicatas)
        link TEXT NOT NULL UNIQUE,
        -- Timestamp de quando o registro foi inserido, com fuso horário (valor padrão: agora)
        scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    # Abre a conexão com o banco de dados usando o gerenciador de contexto (with)
    with get_db_connection() as conn:
        # Abre um cursor para executar comandos SQL
        with conn.cursor() as cur:
            # Executa a consulta de criação da tabela
            cur.execute(sql_create_table)
            # Confirma a transação no banco de dados (salva as alterações)
            conn.commit()
    # Imprime uma mensagem de sucesso após a verificação/criação da tabela
    print("Tabela 'noticias' verificada/criada com sucesso.")

# Função para inserir múltiplas notícias de uma só vez (inserção em lote)
def bulk_insert_news(news_list):
    
    # Verifica se a lista de notícias está vazia
    if not news_list:
        print("Nenhuma notícia nova para inserir.")
        return

    # Definição da consulta SQL para inserção de dados
    sql_insert = """
    INSERT INTO noticias (title, summary, date_text, link)
    VALUES (%s, %s, %s, %s)
    -- Se um link (chave UNIQUE) já existir, não faz nada (ignora a inserção)
    ON CONFLICT (link) DO NOTHING;
    """
    
    conn = None
    try:
        # Tenta obter uma nova conexão com o banco de dados
        conn = get_db_connection()
        # Abre um cursor para executar comandos
        with conn.cursor() as cur:
            
            # Executa a inserção em lote: executa o SQL para cada tupla na 'news_list'
            # Esta é a forma otimizada de inserir múltiplos registros usando psycopg
            cur.executemany(sql_insert, news_list)
            
            # Confirma a transação, salvando todas as inserções no banco
            conn.commit()
            
        # Imprime o número de itens que foram tentados ser inseridos
        print(f"Tentativa de inserção em lote de {len(news_list)} itens concluída.")
        
    except Exception as e:
        # Captura e imprime qualquer erro que ocorra durante a inserção
        print(f"Erro na inserção em lote: {e}")
        # Se houver um erro e a conexão existir, desfaz (rollback) a transação
        if conn:
            conn.rollback() 
    finally:
        # Bloco que sempre será executado, independentemente de erro
        # Garante que a conexão seja fechada se estiver aberta
        if conn:
            conn.close()