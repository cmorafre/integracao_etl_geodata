#!/usr/bin/env python3
"""
Configurações do sistema ETL GEODATA
Centralizadas todas as configurações de conexão e parâmetros
"""

import os
from pathlib import Path

# =====================================
# CONFIGURAÇÕES DE PATHS
# =====================================

# Diretório base do projeto
BASE_DIR = Path(__file__).parent

# Pasta com os scripts SQL (ajuste conforme necessário no servidor)
SQL_SCRIPTS_DIR = "/Users/cmorafre/Development/scripts_geodata"

# Pasta de logs
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# =====================================
# CONFIGURAÇÕES ORACLE (ORIGEM)
# =====================================

ORACLE_CONFIG = {
    'host': '192.168.10.243',
    'port': 1521,
    'service_name': 'ORCL',  # Usando service_name ao invés de SID
    'user': 'GEODATA',
    'password': 'GEo,D4tA0525#!',
    'encoding': 'UTF-8'
}

# =====================================
# CONFIGURAÇÕES POSTGRESQL (DESTINO)
# =====================================

POSTGRESQL_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'geo@2025!@',
    'schema': 'public'
}

# =====================================
# CONFIGURAÇÕES DO ETL
# =====================================

ETL_CONFIG = {
    # Estratégia de carga: 'replace' (DROP/CREATE) ou 'append' (INSERT)
    'load_strategy': 'replace',
    
    # Timeout para queries (em segundos)
    'query_timeout': 300,
    
    # Tamanho do batch para inserção
    'batch_size': 1000,
    
    # Prefixo para tabelas (opcional)
    'table_prefix': '',
    
    # Sufixo para tabelas (opcional) 
    'table_suffix': '',
    
    # Extensões de arquivo SQL aceitas
    'sql_extensions': ['.sql'],
    
    # Arquivos SQL para ignorar (regex patterns)
    'ignore_patterns': [
        r'.*test.*',
        r'.*backup.*',
        r'.*\.bak\.sql$'
    ]
}

# =====================================
# CONFIGURAÇÕES DE LOG
# =====================================

LOG_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
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
