#!/usr/bin/env python3
"""
Script para verificar objetos específicos que causaram erros
Baseado nos erros: ORA-00904 e ORA-00942
"""

import sys
import cx_Oracle
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent))

from config import ORACLE_CONFIG

def connect_oracle():
    """Conecta ao Oracle"""
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

def check_specific_objects():
    """Verifica objetos específicos que causaram erros"""
    print("🔍 VERIFICANDO OBJETOS ESPECÍFICOS DOS ERROS")
    print("="*50)
    
    try:
        conn = connect_oracle()
        cursor = conn.cursor()
        
        # Objetos suspeitos baseados nos erros
        suspected_objects = {
            'QTDE_ENTR_PED_VEN': 'FUNCTION',  # Erro ORA-00904 em carteira_pedido_venda_erp.sql
            'custo_medio': 'FUNCTION',        # Comentário no SQL sugere função customizada
            'table': 'FUNCTION'               # Função table() no SQL
        }
        
        # Tabelas que podem não existir (baseado no erro ORA-00942)
        suspected_tables = [
            'PEDIDO', 'IPEDIDO', 'TRANSAC', 'CADEMP', 'MUNICIPIO', 'PROPRIED', 'CICLO',
            'CONDICAO', 'CFO', 'PESSOAL', 'TIPOOPER', 'INDVALOR', 'INDEXADOR', 
            'PRODSERV', 'GRUPO', 'SUBGRUPO', 'PRODUTO', 'PRINATIVOS', 'CABTAB',
            'NEGOCIACAO', 'CADUSU', 'OCORRENCIAS', 'PREFINAN', 'TOPCTRL',
            'NFENTRA', 'INFENTRA', 'FUNCAOTOPER', 'INOTA', 'NOTA',
            # Tabelas do faturamento_erp.sql
            'NOTACRC', 'CABREC', 'RECEBER', 'DOCDESFAZ', 'CABDESFAZ',
            'RNCCABREC', 'RNCRECEBER'
        ]
        
        print("\n🔧 VERIFICANDO FUNÇÕES:")
        missing_functions = []
        for obj_name, obj_type in suspected_objects.items():
            cursor.execute("""
                SELECT COUNT(*) FROM ALL_OBJECTS 
                WHERE OWNER = USER 
                AND OBJECT_NAME = UPPER(:name)
                AND OBJECT_TYPE = :type
            """, {'name': obj_name, 'type': obj_type})
            
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"   ✅ {obj_name} ({obj_type})")
            else:
                print(f"   ❌ {obj_name} ({obj_type}) - NÃO ENCONTRADA")
                missing_functions.append(obj_name)
        
        print(f"\n📋 VERIFICANDO TABELAS:")
        missing_tables = []
        existing_tables = []
        
        for table_name in suspected_tables:
            cursor.execute("""
                SELECT COUNT(*) FROM ALL_TABLES 
                WHERE OWNER = USER AND TABLE_NAME = UPPER(:name)
            """, {'name': table_name})
            
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"   ✅ {table_name}")
                existing_tables.append(table_name)
            else:
                print(f"   ❌ {table_name} - NÃO ENCONTRADA")
                missing_tables.append(table_name)
        
        # Verificar se existem em outros schemas
        if missing_tables:
            print(f"\n🔍 VERIFICANDO EM OUTROS SCHEMAS:")
            for table_name in missing_tables[:5]:  # Verificar apenas as primeiras 5
                cursor.execute("""
                    SELECT OWNER, TABLE_NAME FROM ALL_TABLES 
                    WHERE TABLE_NAME = UPPER(:name)
                    AND ROWNUM <= 5
                """, {'name': table_name})
                
                results = cursor.fetchall()
                if results:
                    print(f"   🔍 {table_name} encontrada em:")
                    for owner, tbl_name in results:
                        print(f"      • {owner}.{tbl_name}")
                else:
                    print(f"   ❌ {table_name} não encontrada em nenhum schema")
        
        # Verificar usuário atual e suas permissões
        cursor.execute("SELECT USER FROM DUAL")
        current_user = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM ALL_TAB_PRIVS 
            WHERE GRANTEE = USER
        """)
        privileges_count = cursor.fetchone()[0]
        
        print(f"\n👤 INFORMAÇÕES DO USUÁRIO:")
        print(f"   • Usuário conectado: {current_user}")
        print(f"   • Privilégios de tabela: {privileges_count}")
        print(f"   • Tabelas acessíveis: {len(existing_tables)}")
        
        # Resumo final
        print(f"\n📊 RESUMO DOS PROBLEMAS:")
        print(f"   ❌ Funções faltantes: {len(missing_functions)}")
        print(f"   ❌ Tabelas faltantes: {len(missing_tables)}")
        print(f"   ✅ Tabelas encontradas: {len(existing_tables)}")
        
        if missing_functions:
            print(f"\n🔧 FUNÇÕES QUE PRECISAM SER CRIADAS:")
            for func in missing_functions:
                print(f"   • {func}")
        
        if missing_tables:
            print(f"\n📋 TABELAS COM PROBLEMAS:")
            for table in missing_tables[:10]:  # Mostrar apenas as primeiras 10
                print(f"   • {table}")
            
            if len(missing_tables) > 10:
                print(f"   ... e mais {len(missing_tables) - 10} tabelas")
        
        cursor.close()
        conn.close()
        
        return len(missing_functions) + len(missing_tables)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return -1

def main():
    print("🚨 VERIFICAÇÃO RÁPIDA DE OBJETOS FALTANTES")
    print("Baseado nos erros ORA-00904 e ORA-00942")
    print("="*60)
    
    # Mostrar informações dos caminhos
    from config import SQL_SCRIPTS_DIR
    print(f"📁 Diretório SQL configurado: {SQL_SCRIPTS_DIR}")
    
    issues_count = check_specific_objects()
    
    if issues_count == 0:
        print(f"\n🎉 Todos os objetos foram encontrados!")
    elif issues_count > 0:
        print(f"\n💡 SOLUÇÕES RECOMENDADAS:")
        print(f"1. Solicitar ao DBA para criar as funções faltantes")
        print(f"2. Verificar se as tabelas estão em outro schema")
        print(f"3. Solicitar grants de acesso às tabelas necessárias")
        print(f"4. Verificar se o usuário tem permissões adequadas")
        print(f"\n📞 PRÓXIMO PASSO: Contatar administrador do banco Oracle")
    
    return issues_count

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result == 0 else 1)