#!/usr/bin/env python3
"""
Script específico para verificar os objetos que causaram os erros
ORA-00904: "QTDE_ENTR_PED_VEN": invalid identifier
ORA-00942: table or view does not exist
"""

import sys
import cx_Oracle
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent))

from config import ORACLE_CONFIG, SQL_SCRIPTS_DIR

def connect_oracle():
    """Conecta ao Oracle"""
    print("🔌 Conectando ao Oracle...")
    print(f"   Host: {ORACLE_CONFIG['host']}:{ORACLE_CONFIG['port']}")
    print(f"   Service: {ORACLE_CONFIG['service_name']}")
    print(f"   Usuário: {ORACLE_CONFIG['user']}")
    
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

def verify_specific_function():
    """Verifica especificamente a função QTDE_ENTR_PED_VEN"""
    print("\n🔧 VERIFICANDO FUNÇÃO ESPECÍFICA DO ERRO:")
    print("="*50)
    
    try:
        conn = connect_oracle()
        cursor = conn.cursor()
        
        # Verificar função QTDE_ENTR_PED_VEN
        function_name = 'QTDE_ENTR_PED_VEN'
        print(f"🔍 Procurando função: {function_name}")
        
        cursor.execute("""
            SELECT OBJECT_NAME, OBJECT_TYPE, OWNER, STATUS 
            FROM ALL_OBJECTS 
            WHERE OBJECT_NAME = :name
            ORDER BY OWNER
        """, {'name': function_name})
        
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Função {function_name} encontrada:")
            for obj_name, obj_type, owner, status in results:
                print(f"   • {owner}.{obj_name} ({obj_type}) - Status: {status}")
        else:
            print(f"❌ Função {function_name} NÃO ENCONTRADA em nenhum schema")
            
            # Procurar funções similares
            cursor.execute("""
                SELECT OBJECT_NAME, OWNER 
                FROM ALL_OBJECTS 
                WHERE OBJECT_NAME LIKE '%QTDE%' 
                AND OBJECT_TYPE IN ('FUNCTION', 'PROCEDURE')
                AND ROWNUM <= 10
            """)
            
            similar = cursor.fetchall()
            if similar:
                print("💡 Funções similares encontradas:")
                for name, owner in similar:
                    print(f"   • {owner}.{name}")
        
        cursor.close()
        conn.close()
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def verify_sample_tables():
    """Verifica algumas tabelas principais dos SQLs"""
    print("\n📋 VERIFICANDO TABELAS PRINCIPAIS:")
    print("="*50)
    
    # Tabelas principais baseadas nos SQLs
    main_tables = [
        'PEDIDO',       # carteira_pedido_venda_erp.sql
        'IPEDIDO',      # carteira_pedido_venda_erp.sql
        'TRANSAC',      # ambos SQLs
        'NOTA',         # faturamento_erp.sql
        'NFENTRA',      # faturamento_erp.sql
        'CABREC',       # faturamento_erp.sql
        'RECEBER'       # faturamento_erp.sql
    ]
    
    try:
        conn = connect_oracle()
        cursor = conn.cursor()
        
        existing_tables = []
        missing_tables = []
        
        for table_name in main_tables:
            cursor.execute("""
                SELECT COUNT(*) FROM ALL_TABLES 
                WHERE TABLE_NAME = :name
            """, {'name': table_name})
            
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Verificar em qual schema está
                cursor.execute("""
                    SELECT OWNER FROM ALL_TABLES 
                    WHERE TABLE_NAME = :name
                    ORDER BY OWNER
                """, {'name': table_name})
                
                owners = [row[0] for row in cursor.fetchall()]
                print(f"✅ {table_name} - Encontrada em: {', '.join(owners)}")
                existing_tables.append(table_name)
            else:
                print(f"❌ {table_name} - NÃO ENCONTRADA")
                missing_tables.append(table_name)
        
        print(f"\n📊 Resumo das tabelas principais:")
        print(f"   ✅ Encontradas: {len(existing_tables)}")
        print(f"   ❌ Faltantes: {len(missing_tables)}")
        
        cursor.close()
        conn.close()
        
        return len(missing_tables)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return -1

def check_user_permissions():
    """Verifica permissões do usuário atual"""
    print("\n👤 VERIFICANDO PERMISSÕES DO USUÁRIO:")
    print("="*50)
    
    try:
        conn = connect_oracle()
        cursor = conn.cursor()
        
        # Usuário atual
        cursor.execute("SELECT USER FROM DUAL")
        current_user = cursor.fetchone()[0]
        print(f"👤 Usuário conectado: {current_user}")
        
        # Tabelas próprias
        cursor.execute("SELECT COUNT(*) FROM USER_TABLES")
        own_tables = cursor.fetchone()[0]
        print(f"📋 Tabelas próprias: {own_tables}")
        
        # Tabelas com acesso
        cursor.execute("SELECT COUNT(*) FROM ALL_TABLES")
        all_tables = cursor.fetchone()[0]
        print(f"🔓 Tabelas acessíveis: {all_tables}")
        
        # Privilégios
        cursor.execute("SELECT COUNT(*) FROM ALL_TAB_PRIVS WHERE GRANTEE = USER")
        privileges = cursor.fetchone()[0]
        print(f"🔑 Privilégios de tabela: {privileges}")
        
        # Roles
        cursor.execute("""
            SELECT GRANTED_ROLE FROM USER_ROLE_PRIVS 
            WHERE ROWNUM <= 10
        """)
        roles = [row[0] for row in cursor.fetchall()]
        if roles:
            print(f"👥 Roles: {', '.join(roles)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

def main():
    print("🚨 VERIFICAÇÃO ESPECÍFICA DOS ERROS ORACLE")
    print("Focado nos erros ORA-00904 e ORA-00942")
    print("="*60)
    print(f"📁 Diretório SQL: {SQL_SCRIPTS_DIR}")
    
    issues = 0
    
    # 1. Verificar função específica do erro
    function_exists = verify_specific_function()
    if not function_exists:
        issues += 1
    
    # 2. Verificar tabelas principais
    missing_tables_count = verify_sample_tables()
    if missing_tables_count > 0:
        issues += missing_tables_count
    
    # 3. Verificar permissões
    check_user_permissions()
    
    # Resultado final
    print(f"\n{'='*60}")
    print("📋 DIAGNÓSTICO FINAL")
    print(f"{'='*60}")
    
    if issues == 0:
        print("🎉 Nenhum problema crítico encontrado!")
        print("💡 Os erros podem ser de:")
        print("   - Permissões específicas")
        print("   - Schemas diferentes")
        print("   - Sintaxe SQL específica")
    else:
        print(f"❌ Problemas encontrados: {issues}")
        print("\n🔧 SOLUÇÕES RECOMENDADAS:")
        print("1. Criar/instalar função QTDE_ENTR_PED_VEN")
        print("2. Verificar se tabelas estão em outro schema")
        print("3. Solicitar grants apropriados ao DBA")
        print("4. Revisar sintaxe dos SQLs")
    
    return issues

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result == 0 else 1)
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        sys.exit(1)