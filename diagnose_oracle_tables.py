#!/usr/bin/env python3
"""
Script para diagnosticar tabelas e funções faltantes no Oracle
Identifica especificamente quais objetos estão causando os erros
"""

import sys
import cx_Oracle
import re
from pathlib import Path
from datetime import datetime

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent))

from config import ORACLE_CONFIG

def connect_oracle():
    """Conecta ao Oracle e retorna conexão"""
    dsn = cx_Oracle.makedsn(
        ORACLE_CONFIG['host'],
        ORACLE_CONFIG['port'],
        service_name=ORACLE_CONFIG['service_name']
    )
    
    return cx_Oracle.connect(
        user=ORACLE_CONFIG['user'],
        password=ORACLE_CONFIG['password'],
        dsn=dsn
    )

def extract_table_names_from_sql(sql_content):
    """Extrai nomes de tabelas do SQL"""
    # Remove comentários
    sql_clean = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    
    # Padrões para encontrar tabelas
    patterns = [
        r'\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bINNER\s+JOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bLEFT\s+JOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bRIGHT\s+JOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
    ]
    
    tables = set()
    for pattern in patterns:
        matches = re.findall(pattern, sql_clean, re.IGNORECASE)
        for match in matches:
            # Filtrar palavras-chave SQL comuns
            if match.upper() not in ['SELECT', 'WHERE', 'ORDER', 'GROUP', 'HAVING', 'UNION']:
                tables.add(match.upper())
    
    return sorted(list(tables))

def extract_functions_from_sql(sql_content):
    """Extrai funções customizadas do SQL"""
    # Padrão para funções que não são built-in do Oracle
    function_pattern = r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\('
    
    # Remove comentários
    sql_clean = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    
    functions = set()
    matches = re.findall(function_pattern, sql_clean)
    
    # Lista de funções built-in do Oracle (parcial)
    builtin_functions = {
        'SELECT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'SUBSTR', 'LENGTH', 'UPPER', 
        'LOWER', 'TRIM', 'LTRIM', 'RTRIM', 'REPLACE', 'COALESCE', 'NVL', 'DECODE',
        'CASE', 'WHEN', 'TO_CHAR', 'TO_NUMBER', 'TO_DATE', 'SYSDATE', 'TRUNC',
        'ROUND', 'FLOOR', 'CEIL', 'ABS', 'MOD', 'POWER', 'SQRT', 'LPAD', 'RPAD',
        'INSTR', 'LISTAGG', 'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'LEAD', 'LAG',
        'FIRST_VALUE', 'LAST_VALUE', 'EXISTS', 'IN', 'BETWEEN', 'LIKE'
    }
    
    for func in matches:
        if func.upper() not in builtin_functions and len(func) > 2:
            functions.add(func.upper())
    
    return sorted(list(functions))

def check_table_exists(conn, table_name):
    """Verifica se tabela existe"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM ALL_TABLES 
            WHERE OWNER = USER AND TABLE_NAME = :table_name
        """, {'table_name': table_name})
        
        count = cursor.fetchone()[0]
        cursor.close()
        return count > 0
    except:
        return False

def check_function_exists(conn, function_name):
    """Verifica se função existe"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM ALL_OBJECTS 
            WHERE OWNER = USER 
            AND OBJECT_NAME = :func_name 
            AND OBJECT_TYPE IN ('FUNCTION', 'PROCEDURE', 'PACKAGE')
        """, {'func_name': function_name})
        
        count = cursor.fetchone()[0]
        cursor.close()
        return count > 0
    except:
        return False

def get_similar_table_names(conn, table_name):
    """Encontra tabelas similares"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME FROM ALL_TABLES 
            WHERE OWNER = USER 
            AND (TABLE_NAME LIKE :pattern1 OR TABLE_NAME LIKE :pattern2)
            AND ROWNUM <= 5
        """, {
            'pattern1': f'%{table_name[:3]}%',
            'pattern2': f'%{table_name[-3:]}%'
        })
        
        similar = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return similar
    except:
        return []

def diagnose_sql_file(sql_file):
    """Diagnostica um arquivo SQL específico"""
    print(f"\n{'='*60}")
    print(f"🔍 DIAGNOSTICANDO: {Path(sql_file).name}")
    print(f"{'='*60}")
    
    # Ler arquivo
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Extrair tabelas e funções
    tables = extract_table_names_from_sql(sql_content)
    functions = extract_functions_from_sql(sql_content)
    
    print(f"📋 Tabelas encontradas no SQL: {len(tables)}")
    print(f"🔧 Funções encontradas no SQL: {len(functions)}")
    
    # Conectar ao Oracle
    try:
        conn = connect_oracle()
        
        # Verificar tabelas
        print(f"\n📊 VERIFICANDO TABELAS:")
        missing_tables = []
        existing_tables = []
        
        for table in tables:
            exists = check_table_exists(conn, table)
            if exists:
                print(f"   ✅ {table}")
                existing_tables.append(table)
            else:
                print(f"   ❌ {table} - NÃO ENCONTRADA")
                missing_tables.append(table)
                
                # Buscar tabelas similares
                similar = get_similar_table_names(conn, table)
                if similar:
                    print(f"      💡 Tabelas similares: {', '.join(similar)}")
        
        # Verificar funções
        print(f"\n🔧 VERIFICANDO FUNÇÕES:")
        missing_functions = []
        existing_functions = []
        
        for func in functions:
            exists = check_function_exists(conn, func)
            if exists:
                print(f"   ✅ {func}")
                existing_functions.append(func)
            else:
                print(f"   ❌ {func} - NÃO ENCONTRADA")
                missing_functions.append(func)
        
        # Resumo
        print(f"\n📊 RESUMO:")
        print(f"   📋 Tabelas existentes: {len(existing_tables)}/{len(tables)}")
        print(f"   🔧 Funções existentes: {len(existing_functions)}/{len(functions)}")
        
        if missing_tables:
            print(f"\n❌ TABELAS FALTANTES:")
            for table in missing_tables:
                print(f"   • {table}")
        
        if missing_functions:
            print(f"\n❌ FUNÇÕES FALTANTES:")
            for func in missing_functions:
                print(f"   • {func}")
        
        conn.close()
        
        return {
            'missing_tables': missing_tables,
            'missing_functions': missing_functions,
            'total_issues': len(missing_tables) + len(missing_functions)
        }
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return {'error': str(e)}

def main():
    print("🔍 DIAGNÓSTICO DETALHADO DE TABELAS ORACLE")
    print("="*80)
    
    # Arquivos para diagnosticar
    sql_files = [
        "sqls/carteira_pedido_venda_erp.sql",
        "sqls/faturamento_erp.sql"
    ]
    
    total_issues = 0
    all_missing_tables = set()
    all_missing_functions = set()
    
    for sql_file in sql_files:
        if Path(sql_file).exists():
            result = diagnose_sql_file(sql_file)
            
            if 'error' not in result:
                total_issues += result['total_issues']
                all_missing_tables.update(result['missing_tables'])
                all_missing_functions.update(result['missing_functions'])
        else:
            print(f"❌ Arquivo não encontrado: {sql_file}")
    
    # Relatório final
    print(f"\n{'='*80}")
    print("📋 RELATÓRIO FINAL")
    print(f"{'='*80}")
    
    if all_missing_tables:
        print(f"\n❌ TODAS AS TABELAS FALTANTES ({len(all_missing_tables)}):")
        for table in sorted(all_missing_tables):
            print(f"   • {table}")
    
    if all_missing_functions:
        print(f"\n❌ TODAS AS FUNÇÕES FALTANTES ({len(all_missing_functions)}):")
        for func in sorted(all_missing_functions):
            print(f"   • {func}")
    
    if total_issues == 0:
        print("🎉 Nenhum problema encontrado!")
    else:
        print(f"\n📊 Total de problemas: {total_issues}")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("1. Solicitar criação das tabelas faltantes ao DBA")
        print("2. Solicitar criação das funções customizadas")
        print("3. Verificar se há schemas diferentes (ex: schema.tabela)")
        print("4. Verificar permissões de acesso às tabelas")

if __name__ == "__main__":
    main()