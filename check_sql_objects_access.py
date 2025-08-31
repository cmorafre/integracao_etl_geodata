#!/usr/bin/env python3
"""
Script para verificar se o usuário GEODATA tem acesso a todos os objetos
referenciados no arquivo carteira_pedido_venda_erp.sql
"""

import os
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any
from sqlalchemy import create_engine, text
import cx_Oracle

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Configurações carregadas de: {env_path}")
    else:
        print("⚠️  Arquivo .env não encontrado no diretório do projeto")
except ImportError:
    print("⚠️  python-dotenv não instalado, usando variáveis de ambiente do sistema")

def get_oracle_engine():
    """Cria engine SQLAlchemy para Oracle"""
    try:
        oracle_host = os.getenv('ORACLE_HOST')
        oracle_port = int(os.getenv('ORACLE_PORT', '1521'))
        oracle_service = os.getenv('ORACLE_SERVICE_NAME', 'ORCL')
        oracle_user = os.getenv('ORACLE_USER')
        oracle_password = os.getenv('ORACLE_PASSWORD')
        
        if not all([oracle_host, oracle_user, oracle_password]):
            missing = []
            if not oracle_host: missing.append('ORACLE_HOST')
            if not oracle_user: missing.append('ORACLE_USER')
            if not oracle_password: missing.append('ORACLE_PASSWORD')
            raise ValueError(f"Variáveis obrigatórias não definidas: {missing}")
        
        print(f"📡 Conectando em Oracle: {oracle_host}:{oracle_port}/{oracle_service}")
        print(f"👤 Usuário: {oracle_user}")
        
        dsn = cx_Oracle.makedsn(oracle_host, oracle_port, service_name=oracle_service)
        connection_string = f"oracle+cx_oracle://{oracle_user}:{oracle_password}@{dsn}"
        
        engine = create_engine(
            connection_string,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM DUAL"))
        
        print("✅ Conexão Oracle estabelecida com sucesso!")
        return engine
        
    except Exception as e:
        print(f"❌ Erro ao conectar no Oracle: {e}")
        return None

def read_sql_file(sql_file_path: str) -> str:
    """Lê conteúdo do arquivo SQL"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Arquivo SQL lido: {sql_file_path}")
        return content
    except Exception as e:
        print(f"❌ Erro ao ler arquivo SQL: {e}")
        return ""

def extract_bentivi_objects(sql_content: str) -> Dict[str, Set[str]]:
    """Extrai objetos do schema BENTIVI referenciados no SQL"""
    objects = {
        'tables': set(),
        'functions': set(),
        'procedures': set(),
        'views': set()
    }
    
    # Padrões para encontrar objetos BENTIVI
    patterns = {
        'tables': [
            r'FROM\s+BENTIVI\.([A-Z_][A-Z0-9_]*)',
            r'JOIN\s+BENTIVI\.([A-Z_][A-Z0-9_]*)',
            r'INNER\s+JOIN\s+BENTIVI\.([A-Z_][A-Z0-9_]*)',
            r'LEFT\s+JOIN\s+BENTIVI\.([A-Z_][A-Z0-9_]*)',
            r'RIGHT\s+JOIN\s+BENTIVI\.([A-Z_][A-Z0-9_]*)',
            r'UPDATE\s+BENTIVI\.([A-Z_][A-Z0-9_]*)',
            r'INSERT\s+INTO\s+BENTIVI\.([A-Z_][A-Z0-9_]*)',
            r'DELETE\s+FROM\s+BENTIVI\.([A-Z_][A-Z0-9_]*)'
        ],
        'functions': [
            r'BENTIVI\.([A-Z_][A-Z0-9_]*)\s*\(',
            r'TABLE\s*\(\s*BENTIVI\.([A-Z_][A-Z0-9_]*)\s*\('
        ]
    }
    
    # Remover comentários do SQL para análise mais limpa
    sql_clean = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    sql_clean = sql_clean.upper()
    
    # Buscar tabelas e views
    for pattern in patterns['tables']:
        matches = re.findall(pattern, sql_clean, re.IGNORECASE)
        for match in matches:
            objects['tables'].add(match)
    
    # Buscar functions
    for pattern in patterns['functions']:
        matches = re.findall(pattern, sql_clean, re.IGNORECASE)
        for match in matches:
            objects['functions'].add(match)
    
    print(f"📋 Objetos extraídos do SQL:")
    print(f"   • Tabelas/Views: {len(objects['tables'])} encontradas")
    print(f"   • Functions: {len(objects['functions'])} encontradas")
    
    return objects

def check_object_access(engine, object_name: str, object_type: str) -> Dict[str, Any]:
    """Verifica se o usuário GEODATA tem acesso a um objeto específico"""
    queries = {
        'table': """
            SELECT 
                COUNT(*) as has_access,
                'TABLE' as object_type_found
            FROM ALL_TABLES 
            WHERE OWNER = 'BENTIVI' 
            AND TABLE_NAME = :object_name
        """,
        'view': """
            SELECT 
                COUNT(*) as has_access,
                'VIEW' as object_type_found
            FROM ALL_VIEWS 
            WHERE OWNER = 'BENTIVI' 
            AND VIEW_NAME = :object_name
        """,
        'function': """
            SELECT 
                COUNT(*) as has_access,
                OBJECT_TYPE as object_type_found
            FROM ALL_OBJECTS 
            WHERE OWNER = 'BENTIVI' 
            AND OBJECT_NAME = :object_name
            AND OBJECT_TYPE IN ('FUNCTION', 'PROCEDURE', 'PACKAGE')
        """
    }
    
    result = {
        'object_name': object_name,
        'requested_type': object_type,
        'has_access': False,
        'found_type': None,
        'error': None
    }
    
    try:
        # Tentar como tabela primeiro
        with engine.connect() as conn:
            df = pd.read_sql(queries['table'], conn, params={'object_name': object_name})
            if df.iloc[0]['has_access'] > 0:
                result['has_access'] = True
                result['found_type'] = 'TABLE'
                return result
        
        # Tentar como view
        with engine.connect() as conn:
            df = pd.read_sql(queries['view'], conn, params={'object_name': object_name})
            if df.iloc[0]['has_access'] > 0:
                result['has_access'] = True
                result['found_type'] = 'VIEW'
                return result
        
        # Tentar como function/procedure
        with engine.connect() as conn:
            df = pd.read_sql(queries['function'], conn, params={'object_name': object_name})
            if df.iloc[0]['has_access'] > 0:
                result['has_access'] = True
                result['found_type'] = df.iloc[0]['object_type_found']
                return result
                
    except Exception as e:
        result['error'] = str(e)
    
    return result

def generate_access_report(sql_file_path: str, access_results: List[Dict[str, Any]], 
                          extracted_objects: Dict[str, Set[str]]) -> str:
    """Gera relatório de acesso aos objetos"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"sql_objects_access_report_{timestamp}.txt"
    
    # Separar resultados por status
    accessible_objects = [r for r in access_results if r['has_access']]
    inaccessible_objects = [r for r in access_results if not r['has_access']]
    error_objects = [r for r in access_results if r['error']]
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("RELATÓRIO DE ACESSO AOS OBJETOS DO SCHEMA BENTIVI\n")
        f.write("="*80 + "\n")
        f.write(f"Arquivo SQL analisado: {sql_file_path}\n")
        f.write(f"Usuário: GEODATA\n")
        f.write(f"Schema: BENTIVI\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # Resumo executivo
        total_objects = len(access_results)
        accessible_count = len(accessible_objects)
        inaccessible_count = len(inaccessible_objects)
        error_count = len(error_objects)
        
        f.write("📊 RESUMO EXECUTIVO\n")
        f.write("-" * 50 + "\n")
        f.write(f"Total de objetos analisados: {total_objects}\n")
        f.write(f"✅ Objetos acessíveis: {accessible_count}\n")
        f.write(f"❌ Objetos inacessíveis: {inaccessible_count}\n")
        f.write(f"⚠️  Objetos com erro: {error_count}\n")
        f.write(f"\n🎯 STATUS GERAL: ")
        
        if inaccessible_count == 0 and error_count == 0:
            f.write("✅ TODOS OS OBJETOS SÃO ACESSÍVEIS\n")
        else:
            f.write("❌ EXISTEM OBJETOS INACESSÍVEIS\n")
        
        f.write("\n" + "="*80 + "\n\n")
        
        # Função específica QTDE_ENTR_PED_VEN
        qtde_function = None
        for obj in access_results:
            if obj['object_name'] == 'QTDE_ENTR_PED_VEN':
                qtde_function = obj
                break
        
        f.write("🔍 VERIFICAÇÃO ESPECÍFICA: FUNCTION QTDE_ENTR_PED_VEN\n")
        f.write("-" * 60 + "\n")
        if qtde_function:
            if qtde_function['has_access']:
                f.write("✅ FUNCTION QTDE_ENTR_PED_VEN: ACESSÍVEL\n")
                f.write(f"   Tipo encontrado: {qtde_function['found_type']}\n")
            else:
                f.write("❌ FUNCTION QTDE_ENTR_PED_VEN: NÃO ACESSÍVEL\n")
                if qtde_function['error']:
                    f.write(f"   Erro: {qtde_function['error']}\n")
        else:
            f.write("⚠️  FUNCTION QTDE_ENTR_PED_VEN: NÃO ENCONTRADA NA ANÁLISE\n")
        
        f.write("\n" + "="*80 + "\n\n")
        
        # Objetos acessíveis
        if accessible_objects:
            f.write("✅ OBJETOS ACESSÍVEIS\n")
            f.write("="*80 + "\n")
            for i, obj in enumerate(accessible_objects, 1):
                f.write(f"{i:3d}. BENTIVI.{obj['object_name']} ({obj['found_type']})\n")
            f.write(f"\nTotal: {len(accessible_objects)} objetos acessíveis\n")
            f.write("\n" + "="*80 + "\n\n")
        
        # Objetos inacessíveis
        if inaccessible_objects:
            f.write("❌ OBJETOS INACESSÍVEIS\n")
            f.write("="*80 + "\n")
            f.write("⚠️  ATENÇÃO: Estes objetos são referenciados no SQL mas não são acessíveis!\n\n")
            for i, obj in enumerate(inaccessible_objects, 1):
                f.write(f"{i:3d}. BENTIVI.{obj['object_name']} (solicitado como {obj['requested_type']})\n")
                if obj['error']:
                    f.write(f"     Erro: {obj['error']}\n")
            f.write(f"\nTotal: {len(inaccessible_objects)} objetos inacessíveis\n")
            f.write("\n" + "="*80 + "\n\n")
        
        # Análise por tipo de objeto
        f.write("📋 ANÁLISE POR TIPO DE OBJETO\n")
        f.write("-" * 50 + "\n")
        
        for obj_type, objects in extracted_objects.items():
            if objects:
                f.write(f"\n{obj_type.upper()}:\n")
                accessible_of_type = [o for o in accessible_objects if o['requested_type'] == obj_type]
                inaccessible_of_type = [o for o in inaccessible_objects if o['requested_type'] == obj_type]
                
                f.write(f"  Total extraídos: {len(objects)}\n")
                f.write(f"  Acessíveis: {len(accessible_of_type)}\n")
                f.write(f"  Inacessíveis: {len(inaccessible_of_type)}\n")
                
                if inaccessible_of_type:
                    f.write("  ❌ Objetos problemáticos:\n")
                    for obj in inaccessible_of_type:
                        f.write(f"     • {obj['object_name']}\n")
        
        # Conclusão
        f.write("\n" + "="*80 + "\n")
        f.write("📋 CONCLUSÃO\n")
        f.write("="*80 + "\n")
        
        if inaccessible_count == 0 and error_count == 0:
            f.write("✅ O usuário GEODATA tem acesso a TODOS os objetos referenciados\n")
            f.write("   no arquivo carteira_pedido_venda_erp.sql\n")
            f.write("\n🎉 O script SQL deve executar sem problemas de acesso!\n")
        else:
            f.write("❌ O usuário GEODATA NÃO tem acesso a alguns objetos referenciados\n")
            f.write("   no arquivo carteira_pedido_venda_erp.sql\n")
            f.write(f"\n⚠️  {inaccessible_count + error_count} objetos precisam de atenção!\n")
            f.write("\nAções necessárias:\n")
            f.write("• Verificar se os objetos existem no schema BENTIVI\n")
            f.write("• Conceder privilégios necessários ao usuário GEODATA\n")
            f.write("• Verificar sintaxe dos nomes dos objetos no SQL\n")
        
        f.write("\n" + "="*80 + "\n")
    
    print(f"📋 Relatório salvo em: {report_file}")
    return report_file

def main():
    """Função principal"""
    print("🔍 VERIFICAÇÃO DE ACESSO AOS OBJETOS DO SQL")
    print("=" * 80)
    print("📄 Arquivo: carteira_pedido_venda_erp.sql")
    print("👤 Usuário: GEODATA")
    print("🗄️  Schema: BENTIVI")
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Caminho do arquivo SQL
    sql_file_path = "/opt/etl_geodata/sql_scripts/carteira_pedido_venda_erp.sql"
    
    # Verificar se arquivo existe
    if not os.path.exists(sql_file_path):
        sql_file_path = "./sqls/carteira_pedido_venda_erp.sql"  # Fallback local
        if not os.path.exists(sql_file_path):
            print(f"❌ Arquivo SQL não encontrado: {sql_file_path}")
            return
    
    # Conectar ao Oracle
    engine = get_oracle_engine()
    if not engine:
        print("💥 Falha na conexão. Verifique as credenciais no arquivo .env")
        return
    
    try:
        # Ler arquivo SQL
        print("\n" + "="*80)
        print("📖 LENDO E ANALISANDO ARQUIVO SQL")
        print("="*80)
        sql_content = read_sql_file(sql_file_path)
        if not sql_content:
            print("❌ Falha ao ler arquivo SQL")
            return
        
        # Extrair objetos BENTIVI
        extracted_objects = extract_bentivi_objects(sql_content)
        
        # Verificar acesso a cada objeto
        print("\n" + "="*80)
        print("🔐 VERIFICANDO ACESSO AOS OBJETOS")
        print("="*80)
        
        access_results = []
        all_objects = []
        
        # Juntar todos os objetos com seus tipos
        for obj_type, objects in extracted_objects.items():
            for obj_name in objects:
                all_objects.append((obj_name, obj_type))
        
        for obj_name, obj_type in all_objects:
            print(f"🔍 Verificando: BENTIVI.{obj_name} ({obj_type})")
            result = check_object_access(engine, obj_name, obj_type)
            access_results.append(result)
            
            if result['has_access']:
                print(f"   ✅ Acessível como {result['found_type']}")
            else:
                print(f"   ❌ Não acessível")
                if result['error']:
                    print(f"   ⚠️  Erro: {result['error']}")
        
        # Gerar relatório
        print("\n" + "="*80)
        print("📋 GERANDO RELATÓRIO")
        print("="*80)
        report_file = generate_access_report(sql_file_path, access_results, extracted_objects)
        
        # Resumo no console
        accessible_count = len([r for r in access_results if r['has_access']])
        total_count = len(access_results)
        
        print(f"\n🎯 RESULTADO FINAL:")
        print(f"   📊 Objetos analisados: {total_count}")
        print(f"   ✅ Objetos acessíveis: {accessible_count}")
        print(f"   ❌ Objetos inacessíveis: {total_count - accessible_count}")
        
        if accessible_count == total_count:
            print(f"\n🎉 SUCESSO: Todos os objetos são acessíveis!")
        else:
            print(f"\n⚠️  ATENÇÃO: {total_count - accessible_count} objetos não são acessíveis")
            print(f"   Verifique o relatório para detalhes: {report_file}")
        
    except Exception as e:
        print(f"💥 Erro durante a execução: {e}")
        
    finally:
        engine.dispose()
        print("🔐 Conexão Oracle fechada")

if __name__ == "__main__":
    main()