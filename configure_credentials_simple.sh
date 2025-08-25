#!/bin/bash

# =============================================================================
# CONFIGURAÇÃO DE CREDENCIAIS - ETL GEODATA (Versão Simplificada)
# =============================================================================
# Este script configura as credenciais SEM testar conexões
# Use para validar a criação do arquivo .env antes de testar no servidor
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
    
    echo -ne "${CYAN}$prompt${NC}" >&2
    if [ -n "$default" ]; then
        echo -ne " [${YELLOW}$default${NC}]: " >&2
    else
        echo -ne ": " >&2
    fi
    
    read value
    echo "${value:-$default}"
}

# Função para ler senha (mascarada)
read_password() {
    local prompt="$1"
    local password
    
    echo -ne "${CYAN}$prompt${NC}: " >&2
    read -s password
    echo "" >&2  # Nova linha após input mascarado
    echo "$password"
}

# =============================================================================
# INÍCIO DO SCRIPT
# =============================================================================

echo -e "${BLUE}=================================="
echo -e "🔒 CONFIGURAÇÃO DE CREDENCIAIS"
echo -e "     ETL GEODATA (VERSÃO SIMPLES)"
echo -e "==================================${NC}"
echo ""

# Verificar diretório atual
echo -e "${CYAN}📍 Diretório atual: $(pwd)${NC}"
echo ""

echo -e "${CYAN}Este script irá configurar as credenciais de acesso aos bancos de dados.${NC}"
echo -e "${YELLOW}⚠️  IMPORTANTE: Esta versão NÃO testa as conexões!${NC}"
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
# FINALIZAÇÃO
# =============================================================================

echo ""
echo -e "${GREEN}🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📋 ARQUIVO CRIADO:${NC}"
echo -e "${CYAN}• Local: $(pwd)/.env${NC}"
echo -e "${CYAN}• Permissões: 600 (somente proprietário)${NC}"
echo ""
echo -e "${YELLOW}🔧 PRÓXIMOS PASSOS:${NC}"
echo -e "1. Validar arquivo: ${CYAN}cat .env${NC}"
echo -e "2. Testar conexões: ${CYAN}python test_connections.py${NC}"
echo -e "3. Executar ETL teste: ${CYAN}python main.py --dry-run${NC}"
echo -e "4. Executar ETL completo: ${CYAN}python main.py${NC}"
echo ""
echo -e "${GREEN}🔒 Suas credenciais estão salvas em: $(pwd)/.env${NC}"
echo -e "${BLUE}📦 Arquivo .env pronto para uso!${NC}"