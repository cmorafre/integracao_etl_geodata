#!/usr/bin/env python3
"""
Script rápido para testar queries Oracle específicas
Versão simplificada para diagnóstico rápido
"""

import sys
import cx_Oracle
from pathlib import Path
import traceback

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent))

from config import ORACLE_CONFIG

def test_oracle_basic():
    """Teste básico de conexão"""
    try:
        dsn = cx_Oracle.makedsn(
            ORACLE_CONFIG['host'],
            ORACLE_CONFIG['port'],
            service_name=ORACLE_CONFIG['service_name']
        )
        
        conn = cx_Oracle.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=dsn
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        
        print(f"✅ Conexão OK - Data servidor: {result[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro conexão: {e}")
        return False

def test_single_sql(sql_file):
    """Testa um SQL específico"""
    try:
        # Ler arquivo
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read().strip()
        
        print(f"\n🧪 Testando: {Path(sql_file).name}")
        
        # Conectar
        dsn = cx_Oracle.makedsn(
            ORACLE_CONFIG['host'],
            ORACLE_CONFIG['port'],
            service_name=ORACLE_CONFIG['service_name']
        )
        
        conn = cx_Oracle.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=dsn
        )
        
        cursor = conn.cursor()
        
        # Testar com LIMIT 1
        test_query = f"SELECT * FROM ({sql_content}) WHERE ROWNUM <= 1"
        
        cursor.execute(test_query)
        result = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"✅ SQL OK - {len(columns)} colunas retornadas")
        
        cursor.close()
        conn.close()
        return True, None
        
    except cx_Oracle.DatabaseError as e:
        error_obj, = e.args
        error_msg = f"Oracle Error {error_obj.code}: {error_obj.message}"
        print(f"❌ {error_msg}")
        return False, error_msg
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False, str(e)

def main():
    print("🧪 TESTE RÁPIDO ORACLE")
    print("=" * 40)
    
    # Teste conexão
    if not test_oracle_basic():
        sys.exit(1)
    
    # Arquivos para testar
    sql_files = [
        "sql_scripts/carteira_pedido_venda_erp.sql",
        "sql_scripts/faturamento_erp.sql"
    ]
    
    errors = []
    
    for sql_file in sql_files:
        if Path(sql_file).exists():
            success, error = test_single_sql(sql_file)
            if not success:
                errors.append(f"{sql_file}: {error}")
        else:
            print(f"❌ Arquivo não encontrado: {sql_file}")
            errors.append(f"{sql_file}: Arquivo não encontrado")
    
    print(f"\n📋 RESULTADO:")
    if errors:
        print(f"❌ {len(errors)} erro(s) encontrado(s):")
        for error in errors:
            print(f"   • {error}")
        sys.exit(1)
    else:
        print("✅ Todos os SQLs estão funcionando!")
        sys.exit(0)

if __name__ == "__main__":
    main()