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
    echo -e "📥 Baixando Oracle Instant Client..."
    
    # Criar diretório temporário
    TEMP_DIR="/tmp/oracle_setup"
    mkdir -p $TEMP_DIR
    cd $TEMP_DIR
    
    # URLs dos packages Oracle (pode precisar atualizar)
    # Nota: Oracle requer aceitar licença, então pode precisar download manual
    echo -e "${YELLOW}⚠️  Oracle Instant Client precisa ser instalado manualmente:${NC}"
    echo -e "1. Acesse: https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html"
    echo -e "2. Baixe: Basic Package (ZIP) e SQL*Plus Package (ZIP)"
    echo -e "3. Extraia em /opt/oracle/instantclient_21_1/"
    echo -e "4. Configure LD_LIBRARY_PATH"
    
    echo -e "\n${BLUE}🔧 Comandos para configurar Oracle Client:${NC}"
    echo -e "sudo mkdir -p /opt/oracle"
    echo -e "sudo unzip instantclient-basic-linux.x64-21.1.0.0.0.zip -d /opt/oracle/"
    echo -e "sudo unzip instantclient-sqlplus-linux.x64-21.1.0.0.0.zip -d /opt/oracle/"
    echo -e "echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:\$LD_LIBRARY_PATH' >> ~/.bashrc"
    echo -e "echo 'export PATH=/opt/oracle/instantclient_21_1:\$PATH' >> ~/.bashrc"
    echo -e "source ~/.bashrc"
    
    echo -e "\n${YELLOW}⏸️  Pause: Configure Oracle Client manualmente e depois continue${NC}"
    read -p "Pressione Enter quando Oracle Client estiver configurado..."
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
export LD_LIBRARY_PATH="/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH"

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
# 9. TESTES DE CONFIGURAÇÃO
# =============================================================================

echo -e "\n${YELLOW}🧪 9. Executando testes...${NC}"

# Testar imports Python
python -c "
try:
    import pandas, cx_Oracle, psycopg2, sqlalchemy
    print('✅ Todos os imports Python OK')
except ImportError as e:
    print(f'❌ Erro no import: {e}')
    exit(1)
"

# Testar se arquivos principais existem
REQUIRED_FILES=("main.py" "config.py" "etl_functions.py" "test_connections.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}⚠️  Arquivo $file não encontrado. Copie os arquivos Python para $PROJECT_DIR${NC}"
    else
        echo -e "${GREEN}✅ $file encontrado${NC}"
    fi
done

echo -e "${GREEN}✅ Testes de configuração concluídos${NC}"

# =============================================================================
# 10. INFORMAÇÕES FINAIS
# =============================================================================

echo -e "\n${BLUE}=================================="
echo -e "🎉 SETUP CONCLUÍDO!"
echo -e "==================================${NC}"

echo -e "\n${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo -e "1. Copie os arquivos Python (.py) para: $PROJECT_DIR"
echo -e "2. Ajuste o caminho dos scripts SQL em config.py"
echo -e "3. Execute teste de conexão: python test_connections.py"
echo -e "4. Execute teste com arquivo específico: python main.py --file arquivo.sql"
echo -e "5. Configure cron para execução diária"

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