import psycopg
import sys

# --- Variáveis de Configuração da Conexão ---
# As variáveis são autodocumentáveis pelos seus nomes.
DB_HOST = "localhost"
DB_PORT = "5432" 
DB_NAME = "postgres"
DB_USER = "joaog"
DB_PASS = "bmj1212"

def get_db_connection():
    """
    Estabelece e retorna uma nova conexão com o PostgreSQL usando as variáveis de ambiente.
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
        # Mensagem concisa, focada apenas no resultado.
        print("Conexão estabelecida com sucesso.")
        return conn
        
    # Tratamento de erro específico (ex: banco de dados está offline).
    except psycopg.OperationalError as e:
        print("ERRO FATAL: Não foi possível conectar ao banco de dados.")
        # Mantém o detalhe do erro, que é útil para debug.
        print(f"Detalhe: {e}")
        sys.exit(1)