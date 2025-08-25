#!/bin/bash

# =============================================================================
# SCRIPT DE LIMPEZA - ETL GEODATA
# =============================================================================
# Remove arquivos problemáticos e corrige o ambiente
# =============================================================================

echo "🧹 LIMPEZA DO AMBIENTE ETL GEODATA"
echo "=================================="

cd /opt/etl_geodata

# Remover arquivos estranhos criados pelo pip install
echo "🗑️  Removendo arquivos problemáticos..."
rm -f '=1.4.0' '=1.5.0' '=2.8.0' '=2.9.0' '=8.3.0' 2>/dev/null

# Verificar se foram removidos
if ls =* 2>/dev/null; then
    echo "⚠️  Ainda existem arquivos com '=' no nome"
    ls -la =*
else
    echo "✅ Arquivos problemáticos removidos"
fi

# Configurar variáveis Oracle no bashrc se não estiverem
echo "🔧 Configurando Oracle Client no bashrc..."
if ! grep -q "instantclient_19_1" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Oracle Instant Client - ETL GEODATA" >> ~/.bashrc
    echo "export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_1:\$LD_LIBRARY_PATH" >> ~/.bashrc
    echo "export PATH=/opt/oracle/instantclient_19_1:\$PATH" >> ~/.bashrc
    echo "export ORACLE_HOME=/opt/oracle/instantclient_19_1" >> ~/.bashrc
    echo "✅ Variáveis Oracle adicionadas ao bashrc"
else
    echo "✅ Variáveis Oracle já estão no bashrc"
fi

# Aplicar configurações Oracle na sessão atual
export LD_LIBRARY_PATH="/opt/oracle/instantclient_19_1:$LD_LIBRARY_PATH"
export PATH="/opt/oracle/instantclient_19_1:$PATH"
export ORACLE_HOME="/opt/oracle/instantclient_19_1"

# Testar sqlplus
echo "🧪 Testando Oracle Client..."
if command -v sqlplus &> /dev/null; then
    echo "✅ sqlplus encontrado e funcional"
    sqlplus -v
else
    echo "⚠️  sqlplus não encontrado no PATH, mas bibliotecas Oracle estão disponíveis"
fi

# Ativar venv e instalar dependências faltantes
echo "📦 Verificando dependências Python..."
source venv/bin/activate

# Instalar python-dotenv se não estiver
if ! python3 -c "import dotenv" 2>/dev/null; then
    echo "⚠️  Instalando python-dotenv..."
    pip install python-dotenv
    echo "✅ python-dotenv instalado"
else
    echo "✅ python-dotenv já disponível"
fi

# Verificar todas as dependências
echo "🔍 Verificando todas as dependências..."
python3 -c "
import sys
modules = ['pandas', 'cx_Oracle', 'psycopg2', 'sqlalchemy', 'dotenv']
missing = []

for module in modules:
    try:
        __import__(module)
        print(f'✅ {module} disponível')
    except ImportError:
        print(f'❌ {module} NÃO disponível')
        missing.append(module)

if missing:
    print(f'⚠️  Módulos faltando: {missing}')
    sys.exit(1)
else:
    print('🎉 Todas as dependências OK!')
"

deactivate

echo ""
echo "🎯 LIMPEZA CONCLUÍDA!"
echo "===================="
echo "Agora execute: ./configure_credentials.sh"