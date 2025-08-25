#!/bin/bash

# =============================================================================
# SCRIPT DE DEBUG - ETL GEODATA
# =============================================================================
# Use este script para diagnosticar problemas no ambiente
# =============================================================================

echo "🔍 DIAGNÓSTICO DO AMBIENTE ETL GEODATA"
echo "====================================="

# Verificar diretório atual
echo "📍 Diretório atual: $(pwd)"
echo ""

# Verificar arquivos presentes
echo "📋 Arquivos no diretório atual:"
ls -la
echo ""

# Verificar ambiente virtual
echo "🐍 Verificando ambiente virtual:"
if [ -d "venv" ]; then
    echo "✅ Diretório venv encontrado"
    if [ -f "venv/bin/activate" ]; then
        echo "✅ Arquivo activate encontrado"
        echo "📄 Conteúdo do diretório venv/bin:"
        ls -la venv/bin/ | head -10
    else
        echo "❌ Arquivo venv/bin/activate NÃO encontrado"
        echo "📄 Conteúdo do diretório venv:"
        ls -la venv/
    fi
else
    echo "❌ Diretório venv NÃO encontrado"
fi
echo ""

# Verificar Python
echo "🐍 Verificando Python:"
echo "Python3 path: $(which python3)"
python3 --version
echo ""

# Verificar se consegue ativar venv
echo "🧪 Testando ativação do ambiente virtual:"
if [ -f "venv/bin/activate" ]; then
    echo "Tentando ativar venv..."
    source venv/bin/activate && echo "✅ venv ativado com sucesso" || echo "❌ Falha ao ativar venv"
    
    # Verificar módulos Python
    echo ""
    echo "📦 Verificando módulos Python no venv:"
    python3 -c "
try:
    import pandas
    print('✅ pandas disponível')
except ImportError:
    print('❌ pandas NÃO disponível')

try:
    import cx_Oracle
    print('✅ cx_Oracle disponível')
except ImportError as e:
    print(f'❌ cx_Oracle NÃO disponível: {e}')

try:
    import psycopg2
    print('✅ psycopg2 disponível')
except ImportError as e:
    print(f'❌ psycopg2 NÃO disponível: {e}')

try:
    import dotenv
    print('✅ python-dotenv disponível')
except ImportError as e:
    print(f'❌ python-dotenv NÃO disponível: {e}')
"
    
    deactivate 2>/dev/null || true
else
    echo "❌ Não foi possível testar - arquivo activate não existe"
fi
echo ""

# Verificar Oracle Client
echo "🗄️  Verificando Oracle Client:"
if command -v sqlplus &> /dev/null; then
    echo "✅ sqlplus encontrado: $(which sqlplus)"
    sqlplus -v 2>/dev/null || echo "⚠️  sqlplus encontrado mas com problemas"
else
    echo "❌ sqlplus NÃO encontrado"
fi

echo "Verificando LD_LIBRARY_PATH:"
echo "LD_LIBRARY_PATH = $LD_LIBRARY_PATH"

if [ -d "/opt/oracle/instantclient_19_1" ]; then
    echo "✅ Diretório Oracle Client encontrado"
    echo "📄 Arquivos no diretório Oracle:"
    ls -la /opt/oracle/instantclient_19_1/ | head -5
else
    echo "❌ Diretório Oracle Client NÃO encontrado"
fi
echo ""

# Verificar permissões
echo "🔒 Verificando permissões:"
echo "Permissões do configure_credentials.sh:"
ls -la configure_credentials.sh 2>/dev/null || echo "❌ configure_credentials.sh não encontrado"
echo ""

# Tentar executar parte do configure_credentials.sh manualmente
echo "🧪 Teste manual de ativação do venv:"
if [ -f "venv/bin/activate" ]; then
    echo "Executando: source venv/bin/activate"
    (
        source venv/bin/activate
        echo "✅ Ativação bem-sucedida dentro de subshell"
        echo "Python path no venv: $(which python3)"
        echo "Pip path no venv: $(which pip)"
    )
else
    echo "❌ Não foi possível testar - arquivo activate não existe"
fi

echo ""
echo "🎯 DIAGNÓSTICO CONCLUÍDO"
echo "========================="