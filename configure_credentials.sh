#!/bin/bash

# =============================================================================
# CONFIGURAÇÃO DE CREDENCIAIS - ETL GEODATA
# =============================================================================
# Este script configura as credenciais de acesso aos bancos de dados
# Execute após a instalação da infraestrutura (setup.sh)
# =============================================================================

set -e  # Parar se qualquer comando falhar

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para ler entrada com valor padrão
read_with_default() {
    local prompt="$1"
    local default="$2"
    local value
    
    echo -ne "${CYAN}$prompt${NC}"
    if [ -n "$default" ]; then
        echo -ne " [${YELLOW}$default${NC}]: "
    else
        echo -ne ": "
    fi
    
    read value
    echo "${value:-$default}"
}

# Função para ler senha (mascarada)
read_password() {
    local prompt="$1"
    local password
    
    echo -ne "${CYAN}$prompt${NC}: "
    read -s password
    echo  # Nova linha após input mascarado
    echo "$password"
}

# Função para testar conexão Oracle
test_oracle_connection() {
    local host="$1"
    local port="$2"
    local service="$3"
    local user="$4"
    local password="$5"
    
    echo -e "${YELLOW}🧪 Testando conexão Oracle...${NC}"
    echo -e "${CYAN}    Host: $host:$port${NC}"
    echo -e "${CYAN}    Service: $service${NC}"
    echo -e "${CYAN}    User: $user${NC}"
    
    # Verificar se python e módulos necessários estão disponíveis
    if ! python3 -c "import cx_Oracle" 2>/dev/null; then
        echo -e "${RED}❌ Módulo cx_Oracle não encontrado${NC}"
        return 1
    fi
    
    # Usar python para testar conexão com timeout
    timeout 30 python3 << EOF
import os
import sys
try:
    import cx_Oracle
    
    # Configurar variáveis de ambiente temporariamente
    os.environ['ORACLE_HOST'] = '$host'
    os.environ['ORACLE_PORT'] = '$port'
    os.environ['ORACLE_SERVICE_NAME'] = '$service'
    os.environ['ORACLE_USER'] = '$user'
    os.environ['ORACLE_PASSWORD'] = '$password'
    
    # Tentar conexão
    dsn = cx_Oracle.makedsn('$host', '$port', service_name='$service')
    connection = cx_Oracle.connect(user='$user', password='$password', dsn=dsn)
    cursor = connection.cursor()
    cursor.execute("SELECT SYSDATE FROM DUAL")
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    
    print("✅ Conexão Oracle OK!")
    print(f"📅 Data/hora do servidor: {result[0]}")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Erro na conexão Oracle: {e}")
    sys.exit(1)
EOF
}

# Função para testar conexão PostgreSQL
test_postgresql_connection() {
    local host="$1"
    local port="$2"
    local database="$3"
    local user="$4"
    local password="$5"
    
    echo -e "${YELLOW}🧪 Testando conexão PostgreSQL...${NC}"
    echo -e "${CYAN}    Host: $host:$port${NC}"
    echo -e "${CYAN}    Database: $database${NC}"
    echo -e "${CYAN}    User: $user${NC}"
    
    # Verificar se python e módulos necessários estão disponíveis
    if ! python3 -c "import psycopg2" 2>/dev/null; then
        echo -e "${RED}❌ Módulo psycopg2 não encontrado${NC}"
        return 1
    fi
    
    # Usar python para testar conexão com timeout
    timeout 30 python3 << EOF
import sys
try:
    import psycopg2
    
    # Tentar conexão
    connection = psycopg2.connect(
        host='$host',
        port='$port',
        database='$database',
        user='$user',
        password='$password'
    )
    cursor = connection.cursor()
    cursor.execute("SELECT NOW()")
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    
    print("✅ Conexão PostgreSQL OK!")
    print(f"📅 Data/hora do servidor: {result[0]}")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Erro na conexão PostgreSQL: {e}")
    sys.exit(1)
EOF
}

# =============================================================================
# INÍCIO DO SCRIPT
# =============================================================================

echo -e "${BLUE}=================================="
echo -e "🔒 CONFIGURAÇÃO DE CREDENCIAIS"
echo -e "     ETL GEODATA"
echo -e "==================================${NC}"
echo ""

# Verificar se estamos no diretório correto
echo -e "${CYAN}📍 Diretório atual: $(pwd)${NC}"

if [ ! -f "main.py" ] || [ ! -f "config.py" ]; then
    echo -e "${RED}❌ Execute este script no diretório /opt/etl_geodata/${NC}"
    echo -e "${YELLOW}💡 Comando: cd /opt/etl_geodata && ./configure_credentials.sh${NC}"
    
    # Mostrar arquivos presentes para debug
    echo -e "${BLUE}📋 Arquivos encontrados no diretório atual:${NC}"
    ls -la
    exit 1
fi

echo -e "${GREEN}✅ Arquivos principais encontrados${NC}"

# Verificar se ambiente virtual existe e ativar
if [ -d "venv" ]; then
    echo -e "${GREEN}🐍 Ativando ambiente virtual...${NC}"
    
    # Verificar se o activate existe e é executável
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Ambiente virtual ativado${NC}"
        
        # Verificar e instalar python-dotenv se necessário
        if ! python3 -c "import dotenv" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Instalando python-dotenv...${NC}"
            pip install python-dotenv >/dev/null 2>&1
            if python3 -c "import dotenv" 2>/dev/null; then
                echo -e "${GREEN}✅ python-dotenv instalado${NC}"
            else
                echo -e "${YELLOW}⚠️  Falha ao instalar python-dotenv, continuando...${NC}"
            fi
        fi
        
    else
        echo -e "${RED}❌ Arquivo venv/bin/activate não encontrado${NC}"
        echo -e "${YELLOW}💡 Continuando com Python global...${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Ambiente virtual não encontrado${NC}"
    echo -e "${BLUE}💡 Continuando com Python global do sistema${NC}"
fi

# Configurar variáveis de ambiente Oracle
if [ -d "/opt/oracle/instantclient_19_1" ]; then
    echo -e "${BLUE}🔧 Configurando Oracle Client...${NC}"
    export LD_LIBRARY_PATH="/opt/oracle/instantclient_19_1:$LD_LIBRARY_PATH"
    export PATH="/opt/oracle/instantclient_19_1:$PATH"
    export ORACLE_HOME="/opt/oracle/instantclient_19_1"
    echo -e "${GREEN}✅ Variáveis Oracle configuradas${NC}"
fi

echo -e "${CYAN}Este script irá configurar as credenciais de acesso aos bancos de dados.${NC}"
echo -e "${YELLOW}As senhas não serão exibidas na tela por segurança.${NC}"
echo ""
echo -e "${GREEN}🚀 COMO USAR:${NC}"
echo -e "${CYAN}   1. Para cada pergunta, você verá um valor padrão em [amarelo]${NC}"
echo -e "${CYAN}   2. Pressione ENTER para aceitar o padrão${NC}"
echo -e "${CYAN}   3. Ou digite um novo valor para substituir${NC}"
echo -e "${CYAN}   4. As senhas ficarão ocultas quando digitadas${NC}"
echo ""

# =============================================================================
# CONFIGURAÇÕES ORACLE
# =============================================================================

echo -e "${BLUE}📊 CONFIGURAÇÕES ORACLE (Banco de Origem)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${CYAN}💡 Instruções:${NC}"
echo -e "${YELLOW}   • Pressione ENTER para aceitar valores padrão [em amarelo]${NC}"
echo -e "${YELLOW}   • Digite um novo valor para substituir o padrão${NC}"
echo -e "${YELLOW}   • A senha será oculta por segurança${NC}"
echo ""

ORACLE_HOST=$(read_with_default "Host/IP do servidor Oracle" "192.168.10.243")
ORACLE_PORT=$(read_with_default "Porta do Oracle" "1521")
ORACLE_SERVICE_NAME=$(read_with_default "Service Name" "ORCL")
ORACLE_USER=$(read_with_default "Usuário Oracle" "GEODATA")
ORACLE_PASSWORD=$(read_password "Senha Oracle")

if [ -z "$ORACLE_PASSWORD" ]; then
    echo -e "${RED}❌ Senha Oracle é obrigatória!${NC}"
    exit 1
fi

echo ""

# =============================================================================
# CONFIGURAÇÕES POSTGRESQL
# =============================================================================

echo -e "${BLUE}🐘 CONFIGURAÇÕES POSTGRESQL (Banco de Destino)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${CYAN}💡 Configure as credenciais do PostgreSQL:${NC}"
echo ""

POSTGRES_HOST=$(read_with_default "Host/IP do servidor PostgreSQL" "localhost")
POSTGRES_PORT=$(read_with_default "Porta do PostgreSQL" "5432")
POSTGRES_DATABASE=$(read_with_default "Nome do database" "postgres")
POSTGRES_USER=$(read_with_default "Usuário PostgreSQL" "postgres")
POSTGRES_PASSWORD=$(read_password "Senha PostgreSQL")

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo -e "${RED}❌ Senha PostgreSQL é obrigatória!${NC}"
    exit 1
fi

echo ""

# =============================================================================
# CONFIGURAÇÕES OPCIONAIS DO ETL
# =============================================================================

echo -e "${BLUE}⚙️  CONFIGURAÇÕES DO ETL (Opcionais)${NC}"
echo -e "${BLUE}═══════════════════════════════════${NC}"
echo -e "${CYAN}💡 Configure parâmetros do ETL (pode aceitar os padrões):${NC}"
echo ""

ETL_LOAD_STRATEGY=$(read_with_default "Estratégia de carga (replace/append)" "replace")
ETL_QUERY_TIMEOUT=$(read_with_default "Timeout de queries (segundos)" "300")
ETL_BATCH_SIZE=$(read_with_default "Tamanho do batch" "1000")
ETL_LOG_LEVEL=$(read_with_default "Nível de log (DEBUG/INFO/WARNING/ERROR)" "INFO")

echo ""

# =============================================================================
# TESTE DE CONEXÕES
# =============================================================================

echo -e "${YELLOW}🔍 TESTANDO CONEXÕES...${NC}"
echo ""

# Testar Oracle
if ! test_oracle_connection "$ORACLE_HOST" "$ORACLE_PORT" "$ORACLE_SERVICE_NAME" "$ORACLE_USER" "$ORACLE_PASSWORD"; then
    echo -e "${RED}💥 Falha na conexão Oracle!${NC}"
    echo -e "${YELLOW}🔧 Verifique as credenciais e tente novamente.${NC}"
    echo -e "${BLUE}💡 Para reconfigurar: ./configure_credentials.sh${NC}"
    exit 1
fi

echo ""

# Testar PostgreSQL
if ! test_postgresql_connection "$POSTGRES_HOST" "$POSTGRES_PORT" "$POSTGRES_DATABASE" "$POSTGRES_USER" "$POSTGRES_PASSWORD"; then
    echo -e "${RED}💥 Falha na conexão PostgreSQL!${NC}"
    echo -e "${YELLOW}🔧 Verifique as credenciais e tente novamente.${NC}"
    echo -e "${BLUE}💡 Para reconfigurar: ./configure_credentials.sh${NC}"
    exit 1
fi

echo ""

# =============================================================================
# CRIAÇÃO DO ARQUIVO .env
# =============================================================================

echo -e "${YELLOW}📝 Criando arquivo de configuração .env...${NC}"

# Backup do .env anterior se existir
if [ -f ".env" ]; then
    cp .env .env.backup
    echo -e "${GREEN}✅ Backup do .env anterior salvo em .env.backup${NC}"
fi

# Criar novo arquivo .env
cat > .env << EOF
# =============================================================================
# CONFIGURAÇÕES ETL GEODATA - PRODUÇÃO
# =============================================================================
# ⚠️  Este arquivo contém credenciais sensíveis - mantenha seguro!
# 🔒 Criado automaticamente em: $(date)
# =============================================================================

# CONFIGURAÇÕES ORACLE (ORIGEM)
ORACLE_HOST=$ORACLE_HOST
ORACLE_PORT=$ORACLE_PORT
ORACLE_SERVICE_NAME=$ORACLE_SERVICE_NAME
ORACLE_USER=$ORACLE_USER
ORACLE_PASSWORD=$ORACLE_PASSWORD

# CONFIGURAÇÕES POSTGRESQL (DESTINO)
POSTGRES_HOST=$POSTGRES_HOST
POSTGRES_PORT=$POSTGRES_PORT
POSTGRES_DATABASE=$POSTGRES_DATABASE
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# CONFIGURAÇÕES DO ETL
ETL_LOAD_STRATEGY=$ETL_LOAD_STRATEGY
ETL_QUERY_TIMEOUT=$ETL_QUERY_TIMEOUT
ETL_BATCH_SIZE=$ETL_BATCH_SIZE
ETL_LOG_LEVEL=$ETL_LOG_LEVEL

# DIRETÓRIOS
SQL_SCRIPTS_PATH=/opt/etl_geodata/sql_scripts
LOG_DIRECTORY=/opt/etl_geodata/logs

# AMBIENTE
ENV=production
EOF

# Configurar permissões restritas
chmod 600 .env

echo -e "${GREEN}✅ Arquivo .env criado com sucesso!${NC}"
echo -e "${GREEN}🔒 Permissões restritivas aplicadas (600)${NC}"

# =============================================================================
# TESTE FINAL
# =============================================================================

echo ""
echo -e "${YELLOW}🧪 Executando teste final de configuração...${NC}"

# Testar carregamento das configurações
if python3 -c "from config import ORACLE_CONFIG, POSTGRESQL_CONFIG; print('✅ Configurações carregadas com sucesso!')" 2>/dev/null; then
    echo -e "${GREEN}✅ Sistema configurado e funcional!${NC}"
else
    echo -e "${RED}❌ Erro ao carregar configurações!${NC}"
    exit 1
fi

# Desativar ambiente virtual
deactivate

# =============================================================================
# FINALIZAÇÃO
# =============================================================================

echo ""
echo -e "${GREEN}🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo -e "1. Testar conexões: ${CYAN}python test_connections.py${NC}"
echo -e "2. Executar ETL teste: ${CYAN}python main.py --dry-run${NC}"
echo -e "3. Executar ETL completo: ${CYAN}python main.py${NC}"
echo ""
echo -e "${YELLOW}🔧 COMANDOS ÚTEIS:${NC}"
echo -e "• Ativar ambiente virtual: ${CYAN}source venv/bin/activate${NC}"
echo -e "• Ver logs: ${CYAN}tail -f logs/etl_geodata.log${NC}"
echo -e "• Reconfigurar credenciais: ${CYAN}./configure_credentials.sh${NC}"
echo ""
echo -e "${GREEN}🔒 Suas credenciais estão seguras em: /opt/etl_geodata/.env${NC}"
echo -e "${BLUE}🚀 Sistema ETL GEODATA pronto para produção!${NC}"