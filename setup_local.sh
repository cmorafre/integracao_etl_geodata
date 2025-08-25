#!/bin/bash

# =============================================================================
# SETUP LOCAL - ETL GEODATA
# =============================================================================
# Script para configurar ambiente de desenvolvimento local
# Execute apenas em ambiente de desenvolvimento!
# =============================================================================

echo "🚀 CONFIGURAÇÃO LOCAL - ETL GEODATA"
echo "=================================="

# Verificar se já existe arquivo .env
if [ -f ".env" ]; then
    echo "⚠️  Arquivo .env já existe"
    read -p "Deseja sobrescrever? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "Configuração cancelada"
        exit 0
    fi
fi

# Criar arquivo .env para desenvolvimento local
echo "📝 Criando arquivo .env para desenvolvimento..."

cat > .env << 'EOF'
# =============================================================================
# CONFIGURAÇÕES ETL GEODATA - DESENVOLVIMENTO LOCAL
# =============================================================================
# Este arquivo é para desenvolvimento local apenas!
# NÃO commite este arquivo no Git!
# =============================================================================

# CONFIGURAÇÕES ORACLE (ORIGEM)
ORACLE_HOST=192.168.10.243
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_USER=GEODATA
ORACLE_PASSWORD=GEo,D4tA0525#!

# CONFIGURAÇÕES POSTGRESQL (DESTINO) 
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=geo@2025!@

# CONFIGURAÇÕES DO ETL
ETL_LOAD_STRATEGY=replace
ETL_QUERY_TIMEOUT=300
ETL_BATCH_SIZE=100
ETL_LOG_LEVEL=DEBUG

# DIRETÓRIOS (desenvolvimento local)
SQL_SCRIPTS_PATH=./sqls
LOG_DIRECTORY=./logs

# AMBIENTE
ENV=development
EOF

# Configurar permissões restritas
chmod 600 .env

echo "✅ Arquivo .env criado para desenvolvimento"
echo "🔒 Permissões restritivas aplicadas (600)"

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🐍 Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "📦 Instalando dependências..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🎉 CONFIGURAÇÃO LOCAL CONCLUÍDA!"
echo "================================"
echo ""
echo "📋 Para usar:"
echo "1. source venv/bin/activate"
echo "2. python test_connections.py"
echo "3. python main.py --dry-run"
echo ""
echo "🚨 LEMBRE-SE:"
echo "- O arquivo .env contém credenciais sensíveis"
echo "- NUNCA commite o arquivo .env no Git"
echo "- Use apenas em ambiente de desenvolvimento"