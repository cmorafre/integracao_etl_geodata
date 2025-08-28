#!/usr/bin/env python3
"""
Script para verificar se todas as tabelas têm o schema BENTIVI
"""

import re
from pathlib import Path

def extract_tables_without_schema(sql_content):
    """Encontra tabelas que não têm schema"""
    # Remove comentários
    sql_clean = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    
    # Padrões para encontrar tabelas
    patterns = [
        r'\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bINNER\s+JOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bLEFT\s+JOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
    ]
    
    tables_without_schema = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, sql_clean, re.IGNORECASE)
        for match in matches:
            # Verificar se não é palavra-chave SQL e não tem schema
            if (match.upper() not in ['SELECT', 'WHERE', 'ORDER', 'GROUP', 'HAVING', 'UNION', 'ALL'] and
                '.' not in match and  # Não tem schema
                not match.upper().startswith('BENTIVI')):  # Não começa com BENTIVI
                tables_without_schema.add(match.upper())
    
    return sorted(list(tables_without_schema))

def verify_sql_file(sql_file):
    """Verifica um arquivo SQL específico"""
    print(f"\n🔍 Verificando: {sql_file.name}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Contar quantas tabelas têm BENTIVI
    bentivi_count = len(re.findall(r'\bBENTIVI\.', content))
    
    # Encontrar tabelas sem schema
    tables_without_schema = extract_tables_without_schema(content)
    
    print(f"   ✅ Tabelas com BENTIVI: {bentivi_count}")
    
    if tables_without_schema:
        print(f"   ⚠️  Tabelas sem schema: {len(tables_without_schema)}")
        for table in tables_without_schema[:10]:  # Mostrar apenas as primeiras 10
            print(f"      • {table}")
        if len(tables_without_schema) > 10:
            print(f"      ... e mais {len(tables_without_schema) - 10}")
    else:
        print(f"   ✅ Todas as tabelas têm schema!")
    
    return len(tables_without_schema)

def main():
    print("🔍 VERIFICAÇÃO DE SCHEMAS BENTIVI")
    print("="*50)
    
    sql_dir = Path("sqls")
    sql_files = list(sql_dir.glob("*.sql"))
    
    total_issues = 0
    
    for sql_file in sorted(sql_files):
        issues = verify_sql_file(sql_file)
        total_issues += issues
    
    print(f"\n{'='*50}")
    print("📊 RESUMO FINAL")
    print(f"{'='*50}")
    print(f"📁 Arquivos verificados: {len(sql_files)}")
    
    if total_issues == 0:
        print("🎉 Todos os arquivos SQL estão com schemas corretos!")
    else:
        print(f"⚠️  Total de tabelas sem schema: {total_issues}")
    
    return total_issues

if __name__ == "__main__":
    result = main()
    exit(0 if result == 0 else 1)