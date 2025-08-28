#!/usr/bin/env python3
"""
Script para adicionar SCHEMA BENTIVI em todas as tabelas dos arquivos SQL
"""

import re
from pathlib import Path
import os
import shutil
from datetime import datetime

def backup_sql_files(sql_dir):
    """Cria backup dos arquivos SQL originais"""
    backup_dir = Path(sql_dir).parent / "sqls_backup"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"backup_{timestamp}"
    backup_path.mkdir(exist_ok=True)
    
    sql_files = Path(sql_dir).glob("*.sql")
    for sql_file in sql_files:
        shutil.copy2(sql_file, backup_path / sql_file.name)
    
    print(f"✅ Backup criado em: {backup_path}")
    return backup_path

def extract_table_names_from_sql(sql_content):
    """Extrai nomes de tabelas do SQL"""
    # Remove comentários
    sql_clean = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    
    # Padrões para encontrar tabelas (mais abrangente)
    patterns = [
        r'\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bINNER\s+JOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bLEFT\s+JOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bRIGHT\s+JOIN\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bUPDATE\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bINSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)\b',
        r'\bDELETE\s+FROM\s+([A-Za-z_][A-Za-z0-9_]*)\b',
    ]
    
    tables = set()
    for pattern in patterns:
        matches = re.findall(pattern, sql_clean, re.IGNORECASE)
        for match in matches:
            # Filtrar palavras-chave SQL comuns
            if match.upper() not in [
                'SELECT', 'WHERE', 'ORDER', 'GROUP', 'HAVING', 'UNION', 'ALL',
                'DISTINCT', 'TOP', 'LIMIT', 'OFFSET', 'INTO', 'VALUES'
            ]:
                tables.add(match.upper())
    
    return sorted(list(tables))

def add_schema_to_sql(sql_content, schema_name='BENTIVI'):
    """Adiciona schema às tabelas no SQL"""
    
    # Lista de tabelas encontradas no SQL
    tables = extract_table_names_from_sql(sql_content)
    
    print(f"   📋 Tabelas encontradas: {len(tables)}")
    if len(tables) <= 10:
        print(f"      {', '.join(tables)}")
    else:
        print(f"      {', '.join(tables[:10])}... (+{len(tables)-10} mais)")
    
    # Aplicar schema para cada tabela
    modified_sql = sql_content
    modifications = 0
    
    for table in tables:
        # Padrões para substituir (evitar substituir se já tem schema)
        patterns = [
            # FROM tabela
            (rf'\bFROM\s+{re.escape(table)}\b', f'FROM {schema_name}.{table}'),
            # JOIN tabela
            (rf'\bJOIN\s+{re.escape(table)}\b', f'JOIN {schema_name}.{table}'),
            (rf'\bINNER\s+JOIN\s+{re.escape(table)}\b', f'INNER JOIN {schema_name}.{table}'),
            (rf'\bLEFT\s+JOIN\s+{re.escape(table)}\b', f'LEFT JOIN {schema_name}.{table}'),
            (rf'\bRIGHT\s+JOIN\s+{re.escape(table)}\b', f'RIGHT JOIN {schema_name}.{table}'),
            # UPDATE/INSERT/DELETE
            (rf'\bUPDATE\s+{re.escape(table)}\b', f'UPDATE {schema_name}.{table}'),
            (rf'\bINSERT\s+INTO\s+{re.escape(table)}\b', f'INSERT INTO {schema_name}.{table}'),
            (rf'\bDELETE\s+FROM\s+{re.escape(table)}\b', f'DELETE FROM {schema_name}.{table}'),
        ]
        
        for pattern, replacement in patterns:
            # Verificar se já não tem schema (evitar duplicação)
            if not re.search(rf'{re.escape(schema_name)}\.{re.escape(table)}\b', modified_sql, re.IGNORECASE):
                new_sql = re.sub(pattern, replacement, modified_sql, flags=re.IGNORECASE)
                if new_sql != modified_sql:
                    modifications += 1
                    modified_sql = new_sql
    
    print(f"   ✅ Modificações aplicadas: {modifications}")
    return modified_sql

def process_sql_file(sql_file_path, schema_name='BENTIVI'):
    """Processa um arquivo SQL individual"""
    print(f"\n🔄 Processando: {Path(sql_file_path).name}")
    
    # Ler arquivo original
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Aplicar schema
    modified_content = add_schema_to_sql(original_content, schema_name)
    
    # Verificar se houve mudanças
    if modified_content != original_content:
        # Escrever arquivo modificado
        with open(sql_file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"   ✅ Arquivo atualizado com sucesso!")
        return True
    else:
        print(f"   ⚠️  Nenhuma modificação necessária")
        return False

def main():
    print("🔧 ADICIONANDO SCHEMA BENTIVI AOS ARQUIVOS SQL")
    print("="*60)
    
    sql_dir = "sqls"
    schema_name = "BENTIVI"
    
    # Verificar se diretório existe
    if not Path(sql_dir).exists():
        print(f"❌ Diretório não encontrado: {sql_dir}")
        return 1
    
    # Buscar arquivos SQL
    sql_files = list(Path(sql_dir).glob("*.sql"))
    if not sql_files:
        print(f"❌ Nenhum arquivo SQL encontrado em: {sql_dir}")
        return 1
    
    print(f"📁 Diretório: {Path(sql_dir).absolute()}")
    print(f"📋 Arquivos encontrados: {len(sql_files)}")
    print(f"🏷️  Schema a ser aplicado: {schema_name}")
    
    # Criar backup
    backup_path = backup_sql_files(sql_dir)
    
    # Processar cada arquivo
    modified_files = 0
    total_files = 0
    
    for sql_file in sorted(sql_files):
        total_files += 1
        if process_sql_file(sql_file, schema_name):
            modified_files += 1
    
    # Relatório final
    print(f"\n{'='*60}")
    print("📊 RELATÓRIO FINAL")
    print(f"{'='*60}")
    print(f"📋 Total de arquivos: {total_files}")
    print(f"✅ Arquivos modificados: {modified_files}")
    print(f"⚠️  Arquivos inalterados: {total_files - modified_files}")
    print(f"💾 Backup salvo em: {backup_path}")
    
    if modified_files > 0:
        print(f"\n🎉 Processamento concluído!")
        print(f"💡 Todos os arquivos SQL agora usam o schema {schema_name}")
        print(f"📝 Recomendo testar os SQLs antes de usar em produção")
    
    return 0

if __name__ == "__main__":
    exit(main())