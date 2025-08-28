#!/usr/bin/env python3
"""
Script para corrigir tabelas que faltaram o schema BENTIVI
"""

import re
from pathlib import Path
import shutil
from datetime import datetime

def fix_missing_schemas():
    """Corrige schemas faltantes nos arquivos SQL"""
    
    sql_dir = Path("sqls")
    
    # Lista de tabelas que podem estar sem schema
    table_fixes = [
        # Tabelas que comumente ficam sem schema em subqueries ou JOINs específicos
        ('CFO', 'BENTIVI.CFO'),
        ('TRANSAC', 'BENTIVI.TRANSAC'),
        ('NEGOCIACAO', 'BENTIVI.NEGOCIACAO'),
        ('INDVALOR', 'BENTIVI.INDVALOR'),
        ('CABREC', 'BENTIVI.CABREC'),
        ('NOTA N', 'BENTIVI.NOTA N'),
        ('NFENTRA N', 'BENTIVI.NFENTRA N'),
    ]
    
    for sql_file in sql_dir.glob("*.sql"):
        print(f"\n🔄 Verificando: {sql_file.name}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = 0
        
        # Corrigir tabelas específicas que ficaram sem schema
        for old_pattern, new_pattern in table_fixes:
            # Procurar padrões onde a tabela não tem schema
            pattern = rf'\b(?<!BENTIVI\.){re.escape(old_pattern)}\b'
            if re.search(pattern, content):
                content = re.sub(pattern, new_pattern, content)
                fixes_made += 1
        
        # Verificar se houve mudanças
        if content != original_content:
            # Fazer backup antes de alterar
            backup_file = sql_file.with_suffix(f'.sql.bak_{datetime.now().strftime("%H%M%S")}')
            shutil.copy2(sql_file, backup_file)
            
            # Salvar arquivo corrigido
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   ✅ {fixes_made} correções aplicadas")
            print(f"   💾 Backup: {backup_file.name}")
        else:
            print(f"   ✅ Nenhuma correção necessária")

if __name__ == "__main__":
    fix_missing_schemas()