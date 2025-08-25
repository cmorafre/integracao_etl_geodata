#!/bin/bash

# =============================================================================
# SCRIPT DE SETUP - ETL GEODATA
# =============================================================================
# Este script configura o ambiente completo para o ETL GEODATA no Ubuntu
# Execute com: chmod +x setup.sh && ./setup.sh
# =============================================================================

set -e  # Parar se qualquer comando falhar

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================="
echo -e "🚀 SETUP ETL GEODATA"
echo -e "==================================${NC}"

# =============================================================================
# 1. VERIFICAÇÕES INICIAIS
# =============================================================================

echo -e "\n${YELLOW}📋 1. Verificando sistema...${NC}"

# Verificar se é Ubuntu
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    echo -e "${RED}❌ Este script foi feito para Ubuntu. Execute manualmente em outros sistemas.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Sistema Ubuntu detectado${NC}"

# Verificar Python 3.8+
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "🐍 Python versão: $PYTHON_VERSION"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3,8) else 1)' 2>/dev/null; then
    echo -e "${RED}❌ Python 3.8+ requerido. Versão atual: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Versão Python OK${NC}"

# =============================================================================
# 2. INSTALAÇÃO DE DEPENDÊNCIAS DO SISTEMA
# =============================================================================

echo -e "\n${YELLOW}📦 2. Instalando dependências do sistema...${NC}"

sudo apt-get update -q

# Pacotes essenciais
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev \
    libaio1 \
    unzip \
    wget \
    curl \
    cron

echo -e "${GREEN}✅ Dependências do sistema instaladas${NC}"

# =============================================================================
# 3. ORACLE INSTANT CLIENT
# =============================================================================

echo -e "\n${YELLOW}🗄️  3. Configurando Oracle Instant Client...${NC}"

# Verificar se já está instalado
if command -v sqlplus &> /dev/null; then
    echo -e "${GREEN}✅ Oracle Instant Client já instalado${NC}"
else
    echo -e "📥 Instalando Oracle Instant Client automaticamente..."
    
    # Limpar instalação anterior se existir
    if [ -d "/opt/oracle/instantclient_19_1" ]; then
        echo -e "🧹 Removendo instalação anterior do Oracle Client..."
        sudo rm -rf /opt/oracle/instantclient_19_1
    fi
    
    # Criar/recriar diretório Oracle limpo
    sudo mkdir -p /opt/oracle
    
    # Criar diretório temporário
    TEMP_DIR="/tmp/oracle_setup"
    rm -rf $TEMP_DIR  # Limpar se existir
    mkdir -p $TEMP_DIR
    cd $TEMP_DIR
    
    # URLs diretas para Oracle Instant Client (sem necessidade de login Oracle)
    # Usando versão 19.x que é mais estável e amplamente suportada
    ORACLE_VERSION="19.16.0.0.0"
    BASE_URL="https://download.oracle.com/otn_software/linux/instantclient/1916000"
    
    echo -e "📥 Baixando Oracle Instant Client Basic..."
    if ! wget -q --show-progress "${BASE_URL}/instantclient-basic-linux.x64-${ORACLE_VERSION}dbru.zip" -O instantclient-basic.zip; then
        echo -e "${RED}❌ Falha no download do Oracle Client Basic${NC}"
        exit 1
    fi
    
    echo -e "📥 Baixando Oracle Instant Client SQL*Plus..."
    if ! wget -q --show-progress "${BASE_URL}/instantclient-sqlplus-linux.x64-${ORACLE_VERSION}dbru.zip" -O instantclient-sqlplus.zip; then
        echo -e "${RED}❌ Falha no download do Oracle Client SQL*Plus${NC}"
        exit 1
    fi
    
    # Verificar se downloads foram bem-sucedidos
    if [[ -f "instantclient-basic.zip" && -f "instantclient-sqlplus.zip" ]]; then
        echo -e "📂 Extraindo arquivos..."
        sudo unzip -q instantclient-basic.zip -d /opt/oracle/
        sudo unzip -q instantclient-sqlplus.zip -d /opt/oracle/
        
        # Encontrar o diretório criado pelo unzip (pode variar o nome)
        EXTRACTED_DIR=$(sudo find /opt/oracle -maxdepth 1 -name "instantclient_*" -type d | head -1)
        
        if [ -n "$EXTRACTED_DIR" ] && [ "$EXTRACTED_DIR" != "/opt/oracle/instantclient_19_1" ]; then
            echo -e "🔄 Renomeando diretório Oracle Client..."
            sudo mv "$EXTRACTED_DIR" /opt/oracle/instantclient_19_1/
        elif [ -z "$EXTRACTED_DIR" ]; then
            echo -e "${RED}❌ Erro: Diretório do Oracle Client não encontrado após extração${NC}"
            exit 1
        else
            echo -e "✅ Diretório Oracle Client já está no local correto"
        fi
        
        # Configurar variáveis de ambiente (evitando duplicação)
        echo -e "⚙️  Configurando variáveis de ambiente..."
        
        # Remover configurações Oracle antigas do .bashrc se existirem
        grep -v "Oracle Instant Client\|instantclient_19_1\|ORACLE_HOME" ~/.bashrc > ~/.bashrc.tmp || true
        mv ~/.bashrc.tmp ~/.bashrc
        
        # Adicionar novas configurações
        echo "# Oracle Instant Client" >> ~/.bashrc
        echo "export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_1:\$LD_LIBRARY_PATH" >> ~/.bashrc
        echo "export PATH=/opt/oracle/instantclient_19_1:\$PATH" >> ~/.bashrc
        echo "export ORACLE_HOME=/opt/oracle/instantclient_19_1" >> ~/.bashrc
        
        # Aplicar configurações na sessão atual
        export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_1:$LD_LIBRARY_PATH
        export PATH=/opt/oracle/instantclient_19_1:$PATH
        export ORACLE_HOME=/opt/oracle/instantclient_19_1
        
        # Verificar se arquivos foram instalados corretamente
        if [ -f "/opt/oracle/instantclient_19_1/libclntsh.so.19.1" ] && [ -f "/opt/oracle/instantclient_19_1/sqlplus" ]; then
            echo -e "✅ Arquivos Oracle Client encontrados"
            
            # Ajustar permissões
            sudo chmod +x /opt/oracle/instantclient_19_1/sqlplus
            
            # Teste de instalação
            if /opt/oracle/instantclient_19_1/sqlplus -v &> /dev/null; then
                echo -e "${GREEN}✅ Oracle Instant Client instalado e configurado com sucesso${NC}"
            else
                echo -e "${YELLOW}⚠️  Oracle Client instalado, mas pode precisar reiniciar o terminal${NC}"
                echo -e "${BLUE}💡 Execute: source ~/.bashrc${NC}"
            fi
        else
            echo -e "${RED}❌ Erro: Arquivos essenciais do Oracle Client não encontrados${NC}"
            exit 1
        fi
        
        # Limpar arquivos temporários
        cd /
        rm -rf "$TEMP_DIR"
        
    else
        echo -e "${RED}❌ Falha no download do Oracle Client. Tentando instalação manual...${NC}"
        echo -e "${YELLOW}⚠️  Configure Oracle Client manualmente:${NC}"
        echo -e "1. Acesse: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html"
        echo -e "2. Baixe: Basic Package e SQL*Plus Package"
        echo -e "3. Execute os comandos abaixo:"
        echo -e "sudo mkdir -p /opt/oracle"
        echo -e "sudo unzip instantclient-basic-*.zip -d /opt/oracle/"
        echo -e "sudo unzip instantclient-sqlplus-*.zip -d /opt/oracle/"
        echo -e "echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_*:\$LD_LIBRARY_PATH' >> ~/.bashrc"
        echo -e "echo 'export PATH=/opt/oracle/instantclient_*:\$PATH' >> ~/.bashrc"
        echo -e "source ~/.bashrc"
        
        echo -e "\n${YELLOW}⏸️  Pause: Configure Oracle Client manualmente e depois continue${NC}"
        read -p "Pressione Enter quando Oracle Client estiver configurado..."
    fi
fi

# =============================================================================
# 4. AMBIENTE VIRTUAL PYTHON
# =============================================================================

echo -e "\n${YELLOW}🐍 4. Criando ambiente virtual Python...${NC}"

# Diretório do projeto
PROJECT_DIR="/opt/etl_geodata"
VENV_DIR="$PROJECT_DIR/venv"

# Criar diretório do projeto
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

# Criar ambiente virtual
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Ambiente virtual criado${NC}"
else
    echo -e "${GREEN}✅ Ambiente virtual já existe${NC}"
fi

# Ativar ambiente virtual
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

echo -e "${GREEN}✅ Ambiente virtual configurado${NC}"

# =============================================================================
# 5. INSTALAÇÃO DE PACOTES PYTHON
# =============================================================================

echo -e "\n${YELLOW}📚 5. Instalando pacotes Python...${NC}"

# Instalar do requirements.txt se existir, senão instalar manualmente
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    # Instalar pacotes essenciais
    pip install pandas>=1.5.0
    pip install cx_Oracle>=8.3.0
    pip install psycopg2-binary>=2.9.0
    pip install SQLAlchemy>=1.4.0
    pip install python-dateutil>=2.8.0
fi

echo -e "${GREEN}✅ Pacotes Python instalados${NC}"

# =============================================================================
# 6. ESTRUTURA DE DIRETÓRIOS
# =============================================================================

echo -e "\n${YELLOW}📁 6. Criando estrutura de diretórios...${NC}"

mkdir -p logs
mkdir -p backup
mkdir -p temp
mkdir -p sql_scripts

# Ajustar permissões
chmod 755 logs backup temp sql_scripts

echo -e "${GREEN}✅ Estrutura de diretórios criada${NC}"

# =============================================================================
# 7. CONFIGURAÇÃO DO CRON
# =============================================================================

echo -e "\n${YELLOW}⏰ 7. Configurando agendamento (cron)...${NC}"

# Script wrapper para cron
cat > etl_cron.sh << 'EOF'
#!/bin/bash
# Wrapper script para execução via cron

# Definir variáveis de ambiente
export PATH="/opt/etl_geodata/venv/bin:$PATH"
export LD_LIBRARY_PATH="/opt/oracle/instantclient_19_1:$LD_LIBRARY_PATH"
export ORACLE_HOME="/opt/oracle/instantclient_19_1"

# Navegar para diretório do projeto
cd /opt/etl_geodata

# Ativar ambiente virtual
source venv/bin/activate

# Executar ETL
python main.py >> logs/cron.log 2>&1

# Log de execução
echo "$(date): ETL executado via cron" >> logs/cron_history.log
EOF

chmod +x etl_cron.sh

echo -e "${BLUE}📋 Para agendar execução diária às 02:00, execute:${NC}"
echo -e "crontab -e"
echo -e "${BLUE}Adicione a linha:${NC}"
echo -e "0 2 * * * /opt/etl_geodata/etl_cron.sh"

echo -e "${GREEN}✅ Script de cron criado${NC}"

# =============================================================================
# 8. CONFIGURAÇÃO DE LOGS
# =============================================================================

echo -e "\n${YELLOW}📝 8. Configurando logrotate...${NC}"

# Configuração do logrotate
sudo tee /etc/logrotate.d/etl-geodata > /dev/null << EOF
/opt/etl_geodata/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su $USER $USER
}
EOF

echo -e "${GREEN}✅ Logrotate configurado${NC}"

# =============================================================================
# 9. TESTES BÁSICOS DE PYTHON
# =============================================================================

echo -e "\n${YELLOW}🧪 9. Testando imports Python...${NC}"

# Testar imports Python
python -c "
try:
    import pandas, cx_Oracle, psycopg2, sqlalchemy
    print('✅ Todos os imports Python OK')
except ImportError as e:
    print(f'❌ Erro no import: {e}')
    exit(1)
"

echo -e "${GREEN}✅ Testes básicos concluídos${NC}"

# =============================================================================
# 10. CÓPIA DOS ARQUIVOS PYTHON E SQL
# =============================================================================

echo -e "\n${YELLOW}📋 10. Copiando arquivos do projeto...${NC}"

# Detectar diretório de origem do projeto
# O script pode ser executado de diferentes locais após git clone
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "📍 Diretório do script: $SCRIPT_DIR"

# Possíveis locais onde os arquivos podem estar
POSSIBLE_DIRS=(
    "$SCRIPT_DIR"                                    # Mesmo diretório do setup.sh
    "$(pwd)"                                         # Diretório atual
    "$HOME/integracao_etl_geodata"                   # Home do usuário
    "/tmp/integracao_etl_geodata"                    # Temporário
)

SOURCE_DIR=""
SQL_SOURCE_DIR=""

# Procurar diretório com os arquivos do projeto
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [[ -f "$dir/main.py" && -f "$dir/config.py" && -d "$dir/sqls" ]]; then
        SOURCE_DIR="$dir"
        SQL_SOURCE_DIR="$dir/sqls"
        echo -e "📁 Arquivos do projeto encontrados em: $SOURCE_DIR"
        break
    fi
done

if [ -z "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Não foi possível encontrar os arquivos do projeto!${NC}"
    echo -e "${YELLOW}💡 Certifique-se de que os arquivos estão no mesmo diretório do setup.sh${NC}"
    echo -e "${BLUE}📋 Para copiar manualmente:${NC}"
    echo -e "cp /caminho/do/projeto/*.py /opt/etl_geodata/"
    echo -e "cp /caminho/do/projeto/requirements.txt /opt/etl_geodata/"
    echo -e "cp /caminho/do/projeto/sqls/*.sql /opt/etl_geodata/sql_scripts/"
    exit 1
fi

# Copiar arquivos Python principais
echo -e "🐍 Copiando arquivos Python..."
PYTHON_FILES=("main.py" "config.py" "etl_functions.py" "test_connections.py")
for file in "${PYTHON_FILES[@]}"; do
    if [ -f "$SOURCE_DIR/$file" ]; then
        cp "$SOURCE_DIR/$file" .
        echo -e "${GREEN}✅ $file copiado${NC}"
    else
        echo -e "${YELLOW}⚠️  $file não encontrado${NC}"
    fi
done

# Copiar requirements.txt se existir
if [ -f "$SOURCE_DIR/requirements.txt" ]; then
    cp "$SOURCE_DIR/requirements.txt" .
    echo -e "${GREEN}✅ requirements.txt copiado${NC}"
fi

# Copiar arquivos SQL
if [ -d "$SQL_SOURCE_DIR" ]; then
    echo -e "📋 Copiando arquivos SQL..."
    
    if ls "$SQL_SOURCE_DIR"/*.sql 1> /dev/null 2>&1; then
        cp "$SQL_SOURCE_DIR"/*.sql sql_scripts/
        SQL_COUNT=$(ls -1 "$SQL_SOURCE_DIR"/*.sql | wc -l)
        echo -e "${GREEN}✅ ${SQL_COUNT} arquivos SQL copiados para /opt/etl_geodata/sql_scripts/${NC}"
        
        # Listar arquivos copiados
        echo -e "${BLUE}📋 Arquivos SQL copiados:${NC}"
        for sql_file in "$SQL_SOURCE_DIR"/*.sql; do
            filename=$(basename "$sql_file")
            echo -e "   • $filename"
        done
        
        # Ajustar permissões
        chmod 644 sql_scripts/*.sql
        
    else
        echo -e "${YELLOW}⚠️  Nenhum arquivo .sql encontrado em $SQL_SOURCE_DIR${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Pasta 'sqls' não encontrada${NC}"
fi

# Atualizar config.py para usar o diretório correto
if [ -f "config.py" ]; then
    echo -e "⚙️  Atualizando configurações..."
    
    # Backup do config original
    cp config.py config.py.backup
    
    # Substituir o caminho SQL_SCRIPTS_DIR no config.py para usar o diretório de produção
    sed -i 's|SQL_SCRIPTS_DIR = ".*"|SQL_SCRIPTS_DIR = "/opt/etl_geodata/sql_scripts"|g' config.py
    
    echo -e "${GREEN}✅ Configuração atualizada em config.py${NC}"
    echo -e "${BLUE}📋 SQL_SCRIPTS_DIR configurado para: /opt/etl_geodata/sql_scripts${NC}"
fi

# =============================================================================
# 11. VALIDAÇÃO FINAL
# =============================================================================

echo -e "\n${YELLOW}✅ 11. Validação final do setup...${NC}"

# Verificar se todos os arquivos necessários estão no lugar
REQUIRED_FILES=("main.py" "config.py" "etl_functions.py" "test_connections.py")
ALL_FILES_OK=true

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file presente${NC}"
    else
        echo -e "${RED}❌ $file não encontrado${NC}"
        ALL_FILES_OK=false
    fi
done

# Verificar se há arquivos SQL
if ls sql_scripts/*.sql 1> /dev/null 2>&1; then
    SQL_COUNT=$(ls -1 sql_scripts/*.sql | wc -l)
    echo -e "${GREEN}✅ ${SQL_COUNT} arquivos SQL disponíveis${NC}"
else
    echo -e "${YELLOW}⚠️  Nenhum arquivo SQL encontrado${NC}"
fi

# Verificar estrutura de diretórios
REQUIRED_DIRS=("logs" "backup" "temp" "sql_scripts" "venv")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ Diretório $dir criado${NC}"
    else
        echo -e "${RED}❌ Diretório $dir não encontrado${NC}"
    fi
done

# Status final
if [ "$ALL_FILES_OK" = true ]; then
    echo -e "\n${GREEN}🎉 VALIDAÇÃO COMPLETA: Sistema está pronto!${NC}"
else
    echo -e "\n${YELLOW}⚠️  ATENÇÃO: Alguns arquivos estão faltando. Verifique as mensagens acima.${NC}"
fi

# =============================================================================
# 12. INFORMAÇÕES FINAIS
# =============================================================================

echo -e "\n${BLUE}=================================="
echo -e "🎉 SETUP CONCLUÍDO!"
echo -e "==================================${NC}"

echo -e "\n${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo -e "1. ${GREEN}✅ Sistema instalado e configurado automaticamente${NC}"
echo -e "2. Execute teste de conexão: python test_connections.py"
echo -e "3. Execute teste com arquivo específico: python main.py --file nome_arquivo.sql"
echo -e "4. Execute ETL completo: python main.py"
echo -e "5. Configure cron para execução diária: crontab -e"

echo -e "\n${YELLOW}🔧 COMANDOS ÚTEIS:${NC}"
echo -e "• Ativar ambiente virtual: cd $PROJECT_DIR && source venv/bin/activate"
echo -e "• Executar ETL: cd $PROJECT_DIR && python main.py"
echo -e "• Ver logs: tail -f $PROJECT_DIR/logs/etl_geodata.log"
echo -e "• Teste dry-run: python main.py --dry-run"

echo -e "\n${YELLOW}⚙️  CONFIGURAÇÕES:${NC}"
echo -e "• Diretório projeto: $PROJECT_DIR"
echo -e "• Logs: $PROJECT_DIR/logs/"
echo -e "• Script cron: $PROJECT_DIR/etl_cron.sh"
echo -e "• Ambiente virtual: $PROJECT_DIR/venv/"

echo -e "\n${GREEN}✨ Sistema ETL GEODATA pronto para uso!${NC}"

# Desativar ambiente virtual
deactivate

echo -e "\n${BLUE}💡 Para começar:${NC}"
echo -e "cd $PROJECT_DIR"
echo -e "source venv/bin/activate"
echo -e "python test_connections.py"