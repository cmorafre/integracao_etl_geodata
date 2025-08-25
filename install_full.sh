#!/bin/bash

# =============================================================================
# INSTALAÇÃO COMPLETA - ETL GEODATA
# =============================================================================
# Este script faz a instalação completa do sistema ETL GEODATA:
# 1. Instala Git (se necessário)
# 2. Clona repositório do GitHub
# 3. Executa setup.sh completo
# 4. Configura credenciais automaticamente
# =============================================================================

set -e  # Parar se qualquer comando falhar

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configurações do projeto
GITHUB_REPO="https://github.com/cmorafre/integracao_etl_geodata.git"
PROJECT_NAME="integracao_etl_geodata"
INSTALL_DIR="/tmp/etl_install"
FINAL_DIR="/opt/etl_geodata"

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

show_header() {
    echo -e "${BLUE}=================================================================="
    echo -e "🚀 INSTALAÇÃO COMPLETA - ETL GEODATA"
    echo -e "=================================================================="
    echo -e "${CYAN}📦 Repositório: ${GITHUB_REPO}${NC}"
    echo -e "${CYAN}🎯 Destino: ${FINAL_DIR}${NC}"
    echo -e "${BLUE}==================================================================${NC}"
    echo ""
}

log_step() {
    echo -e "${YELLOW}📋 $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_info() {
    echo -e "${CYAN}💡 $1${NC}"
}

# Função para escolher versão do configure_credentials
choose_credentials_version() {
    echo ""
    echo -e "${BLUE}🔒 ESCOLHA A VERSÃO DE CONFIGURAÇÃO DE CREDENCIAIS${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}1) configure_credentials.sh${NC}"
    echo -e "${CYAN}   • Versão completa com teste de conexões${NC}"
    echo -e "${CYAN}   • Valida Oracle e PostgreSQL antes de salvar${NC}"
    echo -e "${CYAN}   • Recomendado para produção${NC}"
    echo ""
    echo -e "${GREEN}2) configure_credentials_simple.sh${NC}"
    echo -e "${CYAN}   • Versão simplificada SEM testes de conexão${NC}"
    echo -e "${CYAN}   • Apenas coleta credenciais e cria .env${NC}"
    echo -e "${CYAN}   • Recomendado para desenvolvimento/teste${NC}"
    echo ""
    
    while true; do
        echo -ne "${YELLOW}Escolha a versão (1 ou 2): ${NC}"
        read -r choice
        case $choice in
            1)
                echo -e "${GREEN}✅ Selecionado: configure_credentials.sh (com testes)${NC}"
                return 1
                ;;
            2)
                echo -e "${GREEN}✅ Selecionado: configure_credentials_simple.sh (sem testes)${NC}"
                return 2
                ;;
            *)
                echo -e "${RED}❌ Opção inválida! Digite 1 ou 2${NC}"
                ;;
        esac
    done
}

# =============================================================================
# INÍCIO DA INSTALAÇÃO
# =============================================================================

show_header

# Verificar se é executado com privilégios adequados
if [[ $EUID -eq 0 ]]; then
   log_error "Este script NÃO deve ser executado como root!"
   log_info "Execute como usuário normal. O script pedirá sudo quando necessário."
   exit 1
fi

# =============================================================================
# 1. VERIFICAÇÕES INICIAIS
# =============================================================================

log_step "1. Verificando sistema..."

# Verificar Ubuntu
if ! grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
    log_error "Este script foi otimizado para Ubuntu"
    log_info "Pode funcionar em outras distribuições, mas não é garantido"
    echo -ne "${YELLOW}Continuar mesmo assim? (y/n): ${NC}"
    read -r continue_anyway
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log_success "Sistema verificado"

# Verificar conexão com internet
log_step "Verificando conexão com internet..."
if ! ping -c 1 github.com &> /dev/null; then
    log_error "Sem conexão com internet ou GitHub inacessível"
    exit 1
fi

log_success "Conexão com internet OK"

# =============================================================================
# 2. INSTALAÇÃO DO GIT
# =============================================================================

log_step "2. Verificando/instalando Git..."

if command -v git &> /dev/null; then
    log_success "Git já instalado: $(git --version)"
else
    log_info "Git não encontrado. Instalando..."
    sudo apt-get update -q
    sudo apt-get install -y git
    
    if command -v git &> /dev/null; then
        log_success "Git instalado com sucesso: $(git --version)"
    else
        log_error "Falha na instalação do Git"
        exit 1
    fi
fi

# =============================================================================
# 3. CLONAGEM DO REPOSITÓRIO
# =============================================================================

log_step "3. Clonando repositório do GitHub..."

# Limpar diretório de instalação se existir
if [ -d "$INSTALL_DIR" ]; then
    log_info "Removendo instalação anterior..."
    rm -rf "$INSTALL_DIR"
fi

# Criar diretório temporário
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Clonar repositório
log_info "Clonando: $GITHUB_REPO"
if git clone "$GITHUB_REPO"; then
    log_success "Repositório clonado com sucesso"
else
    log_error "Falha ao clonar repositório"
    log_info "Verifique se o URL está correto: $GITHUB_REPO"
    exit 1
fi

# Verificar se o clone funcionou
if [ ! -d "$PROJECT_NAME" ]; then
    log_error "Diretório do projeto não encontrado após clone"
    exit 1
fi

cd "$PROJECT_NAME"

# Verificar arquivos essenciais
REQUIRED_FILES=("setup.sh" "main.py" "config.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Arquivo essencial não encontrado: $file"
        exit 1
    fi
done

log_success "Todos os arquivos essenciais encontrados"

# =============================================================================
# 4. EXECUÇÃO DO SETUP.SH
# =============================================================================

log_step "4. Executando instalação da infraestrutura..."

# Tornar setup.sh executável
chmod +x setup.sh

log_info "Iniciando setup.sh..."
echo ""
echo -e "${PURPLE}========================================${NC}"
echo -e "${PURPLE}🔧 EXECUTANDO SETUP DA INFRAESTRUTURA${NC}"
echo -e "${PURPLE}========================================${NC}"
echo ""

# Executar setup.sh
if ./setup.sh; then
    echo ""
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}✅ SETUP DA INFRAESTRUTURA CONCLUÍDO${NC}"  
    echo -e "${PURPLE}========================================${NC}"
    echo ""
    log_success "Infraestrutura instalada com sucesso"
else
    log_error "Falha na instalação da infraestrutura (setup.sh)"
    exit 1
fi

# =============================================================================
# 5. CONFIGURAÇÃO DE CREDENCIAIS
# =============================================================================

log_step "5. Configurando credenciais..."

# Navegar para o diretório final
cd "$FINAL_DIR"

# Verificar se os scripts de credenciais existem
if [ ! -f "configure_credentials.sh" ] || [ ! -f "configure_credentials_simple.sh" ]; then
    log_error "Scripts de configuração de credenciais não encontrados em $FINAL_DIR"
    log_info "Verifique se o setup.sh copiou todos os arquivos corretamente"
    exit 1
fi

# Escolher versão das credenciais
choose_credentials_version
credentials_choice=$?

echo ""
echo -e "${PURPLE}========================================${NC}"
echo -e "${PURPLE}🔒 CONFIGURANDO CREDENCIAIS${NC}"
echo -e "${PURPLE}========================================${NC}"
echo ""

# Executar script de credenciais escolhido
if [ $credentials_choice -eq 1 ]; then
    log_info "Executando configure_credentials.sh (com testes de conexão)..."
    if ./configure_credentials.sh; then
        log_success "Credenciais configuradas com sucesso (com testes)"
    else
        log_error "Falha na configuração das credenciais (versão com testes)"
        log_info "Você pode tentar novamente executando: cd $FINAL_DIR && ./configure_credentials.sh"
        exit 1
    fi
else
    log_info "Executando configure_credentials_simple.sh (sem testes de conexão)..."
    if ./configure_credentials_simple.sh; then
        log_success "Credenciais configuradas com sucesso (sem testes)"
        echo ""
        log_info "⚠️  Lembre-se de testar as conexões posteriormente com:"
        echo -e "${CYAN}cd $FINAL_DIR && source venv/bin/activate && python test_connections.py${NC}"
    else
        log_error "Falha na configuração das credenciais (versão simples)"
        log_info "Você pode tentar novamente executando: cd $FINAL_DIR && ./configure_credentials_simple.sh"
        exit 1
    fi
fi

# =============================================================================
# 6. LIMPEZA E FINALIZAÇÃO
# =============================================================================

log_step "6. Finalizando instalação..."

# Remover diretório temporário
cd /
rm -rf "$INSTALL_DIR"
log_success "Arquivos temporários removidos"

# =============================================================================
# 7. INFORMAÇÕES FINAIS
# =============================================================================

echo ""
echo -e "${GREEN}🎉=================================================================="
echo -e "🎉 INSTALAÇÃO COMPLETA FINALIZADA COM SUCESSO!"
echo -e "🎉==================================================================${NC}"
echo ""

echo -e "${YELLOW}📋 RESUMO DA INSTALAÇÃO:${NC}"
echo -e "${GREEN}✅ Git instalado/verificado${NC}"
echo -e "${GREEN}✅ Repositório clonado de: ${GITHUB_REPO}${NC}"
echo -e "${GREEN}✅ Infraestrutura ETL instalada${NC}"
echo -e "${GREEN}✅ Credenciais configuradas${NC}"
echo -e "${GREEN}✅ Sistema pronto para uso${NC}"
echo ""

echo -e "${YELLOW}📁 LOCALIZAÇÃO DOS ARQUIVOS:${NC}"
echo -e "${CYAN}• Projeto: ${FINAL_DIR}${NC}"
echo -e "${CYAN}• Configurações: ${FINAL_DIR}/.env${NC}"
echo -e "${CYAN}• Logs: ${FINAL_DIR}/logs/${NC}"
echo -e "${CYAN}• Scripts SQL: ${FINAL_DIR}/sql_scripts/${NC}"
echo ""

echo -e "${YELLOW}🚀 PRÓXIMOS PASSOS:${NC}"
echo -e "1. Testar conexões: ${CYAN}cd ${FINAL_DIR} && source venv/bin/activate && python test_connections.py${NC}"
echo -e "2. Executar ETL teste: ${CYAN}cd ${FINAL_DIR} && python main.py --dry-run${NC}"
echo -e "3. Executar ETL completo: ${CYAN}cd ${FINAL_DIR} && python main.py${NC}"
echo -e "4. Configurar agendamento: ${CYAN}crontab -e${NC} (adicione: 0 2 * * * ${FINAL_DIR}/etl_cron.sh)"
echo ""

echo -e "${YELLOW}🔧 COMANDOS ÚTEIS:${NC}"
echo -e "• Ativar ambiente: ${CYAN}cd ${FINAL_DIR} && source venv/bin/activate${NC}"
echo -e "• Ver logs: ${CYAN}tail -f ${FINAL_DIR}/logs/etl_geodata.log${NC}"
echo -e "• Reconfigurar credenciais: ${CYAN}cd ${FINAL_DIR} && ./configure_credentials.sh${NC}"
echo -e "• Status do cron: ${CYAN}crontab -l${NC}"
echo ""

echo -e "${GREEN}🎯 Sistema ETL GEODATA instalado e configurado!${NC}"
echo -e "${BLUE}📖 Consulte o README.md para documentação completa${NC}"