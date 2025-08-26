#!/usr/bin/env python3
"""
Configurações do sistema ETL GEODATA
Centralizadas todas as configurações de conexão e parâmetros

SEGURANÇA:
- Credenciais são carregadas de variáveis de ambiente
- Arquivo .env é usado para desenvolvimento local
- NUNCA commite credenciais no código!
"""

import os
from pathlib import Path
from typing import Dict, Any

# Carregar variáveis de ambiente do arquivo .env se existir
try:
    from dotenv import load_dotenv
    # Procurar arquivo .env no diretório do projeto
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Configurações carregadas de: {env_path}")
    else:
        print("⚠️  Arquivo .env não encontrado, usando variáveis de ambiente do sistema")
except ImportError:
    print("⚠️  python-decouple não instalado, usando variáveis de ambiente do sistema")

# =====================================
# CONFIGURAÇÕES DE PATHS
# =====================================

# Diretório base do projeto
BASE_DIR = Path(__file__).parent

# Pasta com os scripts SQL (prioritiza variável de ambiente)
SQL_SCRIPTS_DIR = os.getenv('SQL_SCRIPTS_PATH', '/opt/etl_geodata/sql_scripts')

# Pasta de logs (prioritiza variável de ambiente)
LOG_DIR = Path(os.getenv('LOG_DIRECTORY', str(BASE_DIR / "logs")))
LOG_DIR.mkdir(exist_ok=True)

# =====================================
# CONFIGURAÇÕES ORACLE (ORIGEM)
# =====================================

def get_oracle_config() -> Dict[str, Any]:
    """
    Carrega configurações Oracle de variáveis de ambiente
    Retorna erro se credenciais obrigatórias não estiverem definidas
    """
    config = {
        'host': os.getenv('ORACLE_HOST'),
        'port': int(os.getenv('ORACLE_PORT', '1521')),
        'service_name': os.getenv('ORACLE_SERVICE_NAME', 'ORCL'),
        'user': os.getenv('ORACLE_USER'),
        'password': os.getenv('ORACLE_PASSWORD'),
        'encoding': 'UTF-8'
    }
    
    # Validar campos obrigatórios
    required_fields = ['host', 'user', 'password']
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        raise ValueError(f"Configurações Oracle obrigatórias não definidas: {missing_fields}. "
                        f"Defina as variáveis de ambiente: {[f'ORACLE_{field.upper()}' for field in missing_fields]}")
    
    return config

# Carregar configurações Oracle
try:
    ORACLE_CONFIG = get_oracle_config()
except ValueError as e:
    print(f"❌ ERRO: {e}")
    # Em desenvolvimento, usar valores padrão com aviso
    if os.getenv('ENV', 'development') == 'development':
        print("🚨 ATENÇÃO: Usando configurações padrão para desenvolvimento!")
        print("🚨 Configure o arquivo .env com suas credenciais reais!")
        ORACLE_CONFIG = {
            'host': '192.168.10.243',
            'port': 1521,
            'service_name': 'ORCL',
            'user': 'GEODATA', 
            'password': 'CONFIGURE_NO_ARQUIVO_ENV',
            'encoding': 'UTF-8'
        }
    else:
        raise

# =====================================
# CONFIGURAÇÕES POSTGRESQL (DESTINO)
# =====================================

def get_postgresql_config() -> Dict[str, Any]:
    """
    Carrega configurações PostgreSQL de variáveis de ambiente
    Retorna erro se credenciais obrigatórias não estiverem definidas
    """
    config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DATABASE', 'postgres'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'schema': 'public'
    }
    
    # Validar campos obrigatórios
    required_fields = ['user', 'password']
    missing_fields = [field for field in required_fields if not config.get(field)]
    
    if missing_fields:
        raise ValueError(f"Configurações PostgreSQL obrigatórias não definidas: {missing_fields}. "
                        f"Defina as variáveis de ambiente: {[f'POSTGRES_{field.upper()}' for field in missing_fields]}")
    
    return config

# Carregar configurações PostgreSQL
try:
    POSTGRESQL_CONFIG = get_postgresql_config()
except ValueError as e:
    print(f"❌ ERRO: {e}")
    # Em desenvolvimento, usar valores padrão com aviso
    if os.getenv('ENV', 'development') == 'development':
        print("🚨 ATENÇÃO: Usando configurações padrão para desenvolvimento!")
        print("🚨 Configure o arquivo .env com suas credenciais reais!")
        POSTGRESQL_CONFIG = {
            'host': 'localhost',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'CONFIGURE_NO_ARQUIVO_ENV',
            'schema': 'public'
        }
    else:
        raise

# =====================================
# CONFIGURAÇÕES DO ETL
# =====================================

ETL_CONFIG = {
    # Estratégia de carga: 'replace' (DROP/CREATE) ou 'append' (INSERT)
    'load_strategy': os.getenv('ETL_LOAD_STRATEGY', 'replace'),
    
    # Timeout para queries (em segundos)
    'query_timeout': int(os.getenv('ETL_QUERY_TIMEOUT', '300')),
    
    # Tamanho do batch para inserção
    'batch_size': int(os.getenv('ETL_BATCH_SIZE', '1000')),
    
    # Prefixo para tabelas (opcional)
    'table_prefix': os.getenv('ETL_TABLE_PREFIX', ''),
    
    # Sufixo para tabelas (opcional) 
    'table_suffix': os.getenv('ETL_TABLE_SUFFIX', ''),
    
    # Extensões de arquivo SQL aceitas
    'sql_extensions': ['.sql'],
    
    # Arquivos SQL para ignorar (regex patterns) - aplicado apenas ao nome do arquivo
    'ignore_patterns': [
        r'^test.*\.sql$',      # Arquivos que começam com "test"
        r'.*_test\.sql$',      # Arquivos que terminam com "_test.sql"
        r'^backup.*\.sql$',    # Arquivos que começam com "backup"
        r'.*_backup\.sql$',    # Arquivos que terminam com "_backup.sql"
        r'.*\.bak\.sql$'       # Arquivos .bak.sql
    ]
}

# =====================================
# CONFIGURAÇÕES DE LOG
# =====================================

LOG_CONFIG = {
    'level': os.getenv('ETL_LOG_LEVEL', 'INFO'),  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'max_file_size': int(os.getenv('LOG_MAX_FILE_SIZE', str(10 * 1024 * 1024))),  # 10MB default
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
    'log_file': LOG_DIR / 'etl_geodata.log'
}

# =====================================
# MAPEAMENTO DE TIPOS DE DADOS
# =====================================

# Mapeamento Oracle -> PostgreSQL
TYPE_MAPPING = {
    # Numéricos
    'NUMBER': 'NUMERIC',
    'INTEGER': 'INTEGER', 
    'INT': 'INTEGER',
    'FLOAT': 'REAL',
    'BINARY_FLOAT': 'REAL',
    'BINARY_DOUBLE': 'DOUBLE PRECISION',
    
    # Texto
    'VARCHAR2': 'VARCHAR',
    'CHAR': 'CHAR',
    'NCHAR': 'CHAR',
    'NVARCHAR2': 'VARCHAR',
    'CLOB': 'TEXT',
    'NCLOB': 'TEXT',
    
    # Data/Hora
    'DATE': 'TIMESTAMP',
    'TIMESTAMP': 'TIMESTAMP',
    'TIMESTAMP WITH TIME ZONE': 'TIMESTAMPTZ',
    'TIMESTAMP WITH LOCAL TIME ZONE': 'TIMESTAMPTZ',
    
    # Binários
    'BLOB': 'BYTEA',
    'RAW': 'BYTEA',
    'LONG RAW': 'BYTEA',
    
    # Outros
    'ROWID': 'VARCHAR(18)',
    'UROWID': 'VARCHAR(4000)'
}

# Tipos padrão para inferência pandas
PANDAS_TO_POSTGRESQL = {
    'object': 'TEXT',
    'int64': 'BIGINT',
    'int32': 'INTEGER',
    'int16': 'SMALLINT',
    'float64': 'DOUBLE PRECISION',
    'float32': 'REAL',
    'bool': 'BOOLEAN',
    'datetime64[ns]': 'TIMESTAMP',
    'timedelta64[ns]': 'INTERVAL'
}

# =====================================
# FUNÇÕES HELPER
# =====================================

def get_oracle_connection_string():
    """Retorna string de conexão Oracle para SQLAlchemy"""
    import cx_Oracle
    dsn = cx_Oracle.makedsn(
        ORACLE_CONFIG['host'], 
        ORACLE_CONFIG['port'], 
        service_name=ORACLE_CONFIG['service_name']
    )
    return f"oracle+cx_oracle://{ORACLE_CONFIG['user']}:{ORACLE_CONFIG['password']}@{dsn}"

def get_postgresql_connection_string():
    """Retorna string de conexão PostgreSQL para SQLAlchemy"""
    return (f"postgresql://{POSTGRESQL_CONFIG['user']}:{POSTGRESQL_CONFIG['password']}"
            f"@{POSTGRESQL_CONFIG['host']}:{POSTGRESQL_CONFIG['port']}"
            f"/{POSTGRESQL_CONFIG['database']}")

def get_table_name_from_file(sql_file_path):
    """Extrai nome da tabela a partir do nome do arquivo SQL"""
    file_name = Path(sql_file_path).stem  # Remove extensão
    
    # Aplica prefixo e sufixo se configurados
    table_name = f"{ETL_CONFIG['table_prefix']}{file_name}{ETL_CONFIG['table_suffix']}"
    
    return table_name.lower()  # PostgreSQL usa lowercase por padrão

# =====================================
# VALIDAÇÕES
# =====================================

def validate_config():
    """Valida se todas as configurações estão corretas"""
    errors = []
    
    # Verifica pasta de scripts SQL
    if not os.path.exists(SQL_SCRIPTS_DIR):
        errors.append(f"Pasta de scripts SQL não encontrada: {SQL_SCRIPTS_DIR}")
    
    # Verifica configurações obrigatórias Oracle
    oracle_required = ['host', 'port', 'service_name', 'user', 'password']
    for field in oracle_required:
        if not ORACLE_CONFIG.get(field):
            errors.append(f"Configuração Oracle obrigatória faltando: {field}")
    
    # Verifica configurações obrigatórias PostgreSQL
    pg_required = ['host', 'port', 'database', 'user', 'password']
    for field in pg_required:
        if not POSTGRESQL_CONFIG.get(field):
            errors.append(f"Configuração PostgreSQL obrigatória faltando: {field}")
    
    return errors

if __name__ == "__main__":
    # Teste das configurações
    errors = validate_config()
    if errors:
        print("❌ Erros de configuração encontrados:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ Configurações válidas!")
        print(f"📁 Scripts SQL: {SQL_SCRIPTS_DIR}")
        print(f"📊 Oracle: {ORACLE_CONFIG['host']}:{ORACLE_CONFIG['port']}")
        print(f"🐘 PostgreSQL: {POSTGRESQL_CONFIG['host']}:{POSTGRESQL_CONFIG['port']}")
