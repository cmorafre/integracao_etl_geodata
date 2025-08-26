#!/bin/bash

# =============================================================================
# CORREÇÃO DE PATHS DO ORACLE INSTANT CLIENT
# =============================================================================
# Script para corrigir problema de biblioteca Oracle não encontrada
# Execute com: chmod +x fix_oracle_paths.sh && ./fix_oracle_paths.sh
# =============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 CORRIGINDO PATHS DO ORACLE INSTANT CLIENT${NC}"
echo -e "=================================================="

# Verificar se Oracle Client existe
if [ ! -d "/opt/oracle/instantclient_19_1" ]; then
    echo -e "${RED}❌ Oracle Instant Client não encontrado em /opt/oracle/instantclient_19_1${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Verificando arquivos Oracle...${NC}"

# Listar arquivos disponíveis
echo -e "📁 Arquivos encontrados:"
ls -la /opt/oracle/instantclient_19_1/ | grep -E "\.(so|dll)" || echo "Nenhuma biblioteca encontrada"

# Criar diretório lib se não existir
echo -e "${YELLOW}📁 Criando diretório lib...${NC}"
sudo mkdir -p /opt/oracle/instantclient_19_1/lib

# Criar links simbólicos para compatibilidade com cx_Oracle
echo -e "${YELLOW}🔗 Criando links simbólicos...${NC}"

# Verificar se biblioteca principal existe
if [ -f "/opt/oracle/instantclient_19_1/libclntsh.so.19.1" ]; then
    sudo ln -sf /opt/oracle/instantclient_19_1/libclntsh.so.19.1 /opt/oracle/instantclient_19_1/lib/libclntsh.so
    sudo ln -sf /opt/oracle/instantclient_19_1/libclntsh.so.19.1 /opt/oracle/instantclient_19_1/libclntsh.so
    echo -e "${GREEN}✅ Link libclntsh.so criado${NC}"
else
    echo -e "${RED}❌ libclntsh.so.19.1 não encontrado${NC}"
fi

# Link para libocci se existir
if [ -f "/opt/oracle/instantclient_19_1/libocci.so.19.1" ]; then
    sudo ln -sf /opt/oracle/instantclient_19_1/libocci.so.19.1 /opt/oracle/instantclient_19_1/lib/libocci.so
    sudo ln -sf /opt/oracle/instantclient_19_1/libocci.so.19.1 /opt/oracle/instantclient_19_1/libocci.so
    echo -e "${GREEN}✅ Link libocci.so criado${NC}"
fi

# Configurar variáveis de ambiente
echo -e "${YELLOW}⚙️  Configurando variáveis de ambiente...${NC}"

# Verificar se já estão no .bashrc
if ! grep -q "instantclient_19_1" ~/.bashrc; then
    echo "# Oracle Instant Client" >> ~/.bashrc
    echo "export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_1:\$LD_LIBRARY_PATH" >> ~/.bashrc
    echo "export PATH=/opt/oracle/instantclient_19_1:\$PATH" >> ~/.bashrc
    echo "export ORACLE_HOME=/opt/oracle/instantclient_19_1" >> ~/.bashrc
    echo -e "${GREEN}✅ Variáveis adicionadas ao .bashrc${NC}"
else
    echo -e "${GREEN}✅ Variáveis já configuradas${NC}"
fi

# Aplicar na sessão atual
export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_1:$LD_LIBRARY_PATH
export PATH=/opt/oracle/instantclient_19_1:$PATH
export ORACLE_HOME=/opt/oracle/instantclient_19_1

echo -e "${YELLOW}🧪 Testando configuração...${NC}"

# Testar se arquivos estão acessíveis
if [ -f "/opt/oracle/instantclient_19_1/lib/libclntsh.so" ]; then
    echo -e "${GREEN}✅ libclntsh.so encontrado em /opt/oracle/instantclient_19_1/lib/${NC}"
else
    echo -e "${RED}❌ libclntsh.so não encontrado em /opt/oracle/instantclient_19_1/lib/${NC}"
fi

# Verificar se libaio está instalado
echo -e "${YELLOW}🔍 Verificando biblioteca libaio...${NC}"
if ! ldconfig -p | grep -q "libaio.so.1"; then
    echo -e "${YELLOW}📦 Instalando libaio necessário para Oracle...${NC}"
    
    # Tentar instalar libaio1t64 primeiro (Ubuntu 24.04+)
    if sudo apt-get update -q && sudo apt-get install -y libaio1t64 2>/dev/null; then
        echo -e "${GREEN}✅ libaio1t64 instalado${NC}"
    # Se falhar, tentar libaio1 (versões mais antigas)
    elif sudo apt-get install -y libaio1 2>/dev/null; then
        echo -e "${GREEN}✅ libaio1 instalado${NC}"
    else
        echo -e "${RED}❌ Falha ao instalar libaio${NC}"
        echo -e "${YELLOW}💡 Execute manualmente: sudo apt-get install libaio1t64${NC}"
    fi
    
    # Criar link simbólico se necessário
    if [ ! -f "/usr/lib/x86_64-linux-gnu/libaio.so.1" ] && [ -f "/usr/lib/x86_64-linux-gnu/libaio.so.1t64" ]; then
        echo -e "${YELLOW}🔗 Criando link simbólico para libaio...${NC}"
        sudo ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1
    fi
fi

# Testar sqlplus
if command -v sqlplus &> /dev/null; then
    echo -e "${GREEN}✅ sqlplus encontrado no PATH${NC}"
    echo -e "${YELLOW}🧪 Testando sqlplus...${NC}"
    if sqlplus -v 2>/dev/null; then
        echo -e "${GREEN}✅ sqlplus funcionando corretamente${NC}"
    else
        echo -e "${RED}❌ Erro ao executar sqlplus${NC}"
        echo -e "${YELLOW}💡 Pode ser necessário instalar/corrigir libaio${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  sqlplus não encontrado no PATH atual${NC}"
fi

echo ""
echo -e "${GREEN}🎉 CORREÇÃO CONCLUÍDA!${NC}"
echo -e "=================================================="
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo -e "1. Recarregar variáveis: ${BLUE}source ~/.bashrc${NC}"
echo -e "2. Testar conexões: ${BLUE}cd /opt/etl_geodata && ./configure_credentials.sh${NC}"
echo ""
echo -e "${BLUE}💡 Se ainda houver erro, reinicie o terminal e tente novamente.${NC}"