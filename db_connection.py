# Importa o driver assíncrono do PostgreSQL para Python
import psycopg
# Importa o módulo 'sys' para interagir com o sistema (encerrar o script)
import sys

# --- Variáveis de Configuração da Conexão com o Banco de Dados ---
# Baseado nas configurações do docker-compose.yml

# Endereço do host do banco de dados (o 'localhost' é a porta exposta no host)
DB_HOST = "localhost"
# Porta do PostgreSQL exposta no host
DB_PORT = "5432" 
# Nome do banco de dados
DB_NAME = "postgres"
# Nome do usuário do banco de dados
DB_USER = "joaog"
# Senha do usuário do banco de dados
DB_PASS = "bmj1212"

# Função para estabelecer e retornar a conexão com o PostgreSQL
def get_db_connection():
    
    # Tenta estabelecer a conexão com o banco de dados
    try:
        # Chama a função connect do psycopg, passando as credenciais
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        # Imprime uma mensagem de sucesso
        print ("Conectado com Sucesso")
        # Retorna o objeto de conexão
        return conn
        
    # Captura o erro específico que ocorre quando a conexão falha (ex: banco offline)
    except psycopg.OperationalError as e:
        # Imprime uma mensagem de erro clara
        print(f"Erro: Não foi possível conectar ao banco de dados.")
        # Imprime os detalhes técnicos do erro
        print(f"Detalhe: {e}")
        # Encerra o script com código de erro 1 (falha)
        sys.exit(1)