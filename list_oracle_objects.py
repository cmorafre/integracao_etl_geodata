#!/usr/bin/env python3
"""
Script para listar todos os objetos Oracle acessíveis pelo usuário GEODATA
Utiliza as credenciais do arquivo .env do projeto ETL GEODATA
"""

import os
import cx_Oracle
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    # Procurar arquivo .env no diretório do projeto
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Configurações carregadas de: {env_path}")
    else:
        print("⚠️  Arquivo .env não encontrado no diretório do projeto")
        print("⚠️  Tentando usar variáveis de ambiente do sistema...")
except ImportError:
    print("⚠️  python-dotenv não instalado, usando variáveis de ambiente do sistema")

def get_oracle_connection():
    """Cria conexão com Oracle usando credenciais do .env"""
    try:
        oracle_host = os.getenv('ORACLE_HOST')
        oracle_port = int(os.getenv('ORACLE_PORT', '1521'))
        oracle_service = os.getenv('ORACLE_SERVICE_NAME', 'ORCL')
        oracle_user = os.getenv('ORACLE_USER')
        oracle_password = os.getenv('ORACLE_PASSWORD')
        
        # Validar credenciais obrigatórias
        if not all([oracle_host, oracle_user, oracle_password]):
            missing = []
            if not oracle_host: missing.append('ORACLE_HOST')
            if not oracle_user: missing.append('ORACLE_USER')
            if not oracle_password: missing.append('ORACLE_PASSWORD')
            raise ValueError(f"Variáveis de ambiente obrigatórias não definidas: {missing}")
        
        print(f"📡 Conectando em Oracle: {oracle_host}:{oracle_port}/{oracle_service}")
        print(f"👤 Usuário: {oracle_user}")
        
        # Criar DSN e conexão
        dsn = cx_Oracle.makedsn(oracle_host, oracle_port, service_name=oracle_service)
        connection = cx_Oracle.connect(user=oracle_user, password=oracle_password, dsn=dsn)
        
        print("✅ Conexão Oracle estabelecida com sucesso!")
        return connection
        
    except Exception as e:
        print(f"❌ Erro ao conectar no Oracle: {e}")
        return None

def execute_query_to_dataframe(connection, query: str, description: str) -> pd.DataFrame:
    """Executa query e retorna DataFrame"""
    try:
        print(f"🔍 Executando consulta: {description}")
        df = pd.read_sql(query, connection)
        print(f"   📊 {len(df)} registros encontrados")
        return df
    except Exception as e:
        print(f"   ❌ Erro na consulta {description}: {e}")
        return pd.DataFrame()

def get_user_owned_objects(connection) -> Dict[str, pd.DataFrame]:
    """Obtém objetos que pertencem ao usuário GEODATA"""
    queries = {
        'tables': {
            'query': """
                SELECT 
                    TABLE_NAME as OBJECT_NAME,
                    'TABLE' as OBJECT_TYPE,
                    NUM_ROWS,
                    LAST_ANALYZED,
                    TABLESPACE_NAME,
                    STATUS
                FROM USER_TABLES 
                ORDER BY TABLE_NAME
            """,
            'description': 'Tabelas do usuário'
        },
        'views': {
            'query': """
                SELECT 
                    VIEW_NAME as OBJECT_NAME,
                    'VIEW' as OBJECT_TYPE,
                    TEXT_LENGTH,
                    READ_ONLY
                FROM USER_VIEWS 
                ORDER BY VIEW_NAME
            """,
            'description': 'Views do usuário'
        },
        'sequences': {
            'query': """
                SELECT 
                    SEQUENCE_NAME as OBJECT_NAME,
                    'SEQUENCE' as OBJECT_TYPE,
                    MIN_VALUE,
                    MAX_VALUE,
                    INCREMENT_BY,
                    LAST_NUMBER
                FROM USER_SEQUENCES 
                ORDER BY SEQUENCE_NAME
            """,
            'description': 'Sequences do usuário'
        },
        'procedures': {
            'query': """
                SELECT 
                    OBJECT_NAME,
                    OBJECT_TYPE,
                    STATUS,
                    CREATED,
                    LAST_DDL_TIME
                FROM USER_OBJECTS 
                WHERE OBJECT_TYPE IN ('PROCEDURE', 'FUNCTION', 'PACKAGE', 'PACKAGE BODY', 'TRIGGER')
                ORDER BY OBJECT_TYPE, OBJECT_NAME
            """,
            'description': 'Procedures, Functions, Packages e Triggers do usuário'
        },
        'indexes': {
            'query': """
                SELECT 
                    INDEX_NAME as OBJECT_NAME,
                    'INDEX' as OBJECT_TYPE,
                    TABLE_NAME,
                    INDEX_TYPE,
                    UNIQUENESS,
                    STATUS
                FROM USER_INDEXES 
                ORDER BY TABLE_NAME, INDEX_NAME
            """,
            'description': 'Índices do usuário'
        },
        'constraints': {
            'query': """
                SELECT 
                    CONSTRAINT_NAME as OBJECT_NAME,
                    'CONSTRAINT' as OBJECT_TYPE,
                    TABLE_NAME,
                    CONSTRAINT_TYPE,
                    STATUS,
                    VALIDATED
                FROM USER_CONSTRAINTS 
                ORDER BY TABLE_NAME, CONSTRAINT_NAME
            """,
            'description': 'Constraints do usuário'
        }
    }
    
    print("\n" + "="*60)
    print("📋 OBJETOS PERTENCENTES AO USUÁRIO GEODATA")
    print("="*60)
    
    results = {}
    for category, info in queries.items():
        df = execute_query_to_dataframe(connection, info['query'], info['description'])
        results[category] = df
    
    return results

def get_accessible_objects(connection) -> Dict[str, pd.DataFrame]:
    """Obtém objetos de outros schemas que o usuário pode acessar"""
    queries = {
        'accessible_tables': {
            'query': """
                SELECT 
                    OWNER,
                    TABLE_NAME as OBJECT_NAME,
                    'TABLE' as OBJECT_TYPE,
                    NUM_ROWS,
                    LAST_ANALYZED,
                    TABLESPACE_NAME
                FROM ALL_TABLES 
                WHERE OWNER != USER
                ORDER BY OWNER, TABLE_NAME
            """,
            'description': 'Tabelas acessíveis de outros schemas'
        },
        'accessible_views': {
            'query': """
                SELECT 
                    OWNER,
                    VIEW_NAME as OBJECT_NAME,
                    'VIEW' as OBJECT_TYPE,
                    TEXT_LENGTH,
                    READ_ONLY
                FROM ALL_VIEWS 
                WHERE OWNER != USER
                ORDER BY OWNER, VIEW_NAME
            """,
            'description': 'Views acessíveis de outros schemas'
        },
        'accessible_sequences': {
            'query': """
                SELECT 
                    SEQUENCE_OWNER as OWNER,
                    SEQUENCE_NAME as OBJECT_NAME,
                    'SEQUENCE' as OBJECT_TYPE,
                    MIN_VALUE,
                    MAX_VALUE,
                    INCREMENT_BY,
                    LAST_NUMBER
                FROM ALL_SEQUENCES 
                WHERE SEQUENCE_OWNER != USER
                ORDER BY SEQUENCE_OWNER, SEQUENCE_NAME
            """,
            'description': 'Sequences acessíveis de outros schemas'
        }
    }
    
    print("\n" + "="*60)
    print("🔓 OBJETOS ACESSÍVEIS DE OUTROS SCHEMAS")
    print("="*60)
    
    results = {}
    for category, info in queries.items():
        df = execute_query_to_dataframe(connection, info['query'], info['description'])
        results[category] = df
    
    return results

def get_user_privileges(connection) -> Dict[str, pd.DataFrame]:
    """Obtém privilégios do usuário"""
    queries = {
        'table_privileges': {
            'query': """
                SELECT 
                    OWNER,
                    TABLE_NAME,
                    PRIVILEGE,
                    GRANTABLE,
                    GRANTOR
                FROM USER_TAB_PRIVS 
                ORDER BY OWNER, TABLE_NAME, PRIVILEGE
            """,
            'description': 'Privilégios em tabelas/views'
        },
        'system_privileges': {
            'query': """
                SELECT 
                    PRIVILEGE,
                    ADMIN_OPTION
                FROM USER_SYS_PRIVS 
                ORDER BY PRIVILEGE
            """,
            'description': 'Privilégios de sistema'
        },
        'role_privileges': {
            'query': """
                SELECT 
                    GRANTED_ROLE,
                    ADMIN_OPTION,
                    DEFAULT_ROLE
                FROM USER_ROLE_PRIVS 
                ORDER BY GRANTED_ROLE
            """,
            'description': 'Roles atribuídas'
        }
    }
    
    print("\n" + "="*60)
    print("🔐 PRIVILÉGIOS DO USUÁRIO")
    print("="*60)
    
    results = {}
    for category, info in queries.items():
        df = execute_query_to_dataframe(connection, info['query'], info['description'])
        results[category] = df
    
    return results

def generate_summary(all_results: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, Any]:
    """Gera resumo dos resultados"""
    summary = {
        'execution_time': datetime.now().isoformat(),
        'user': os.getenv('ORACLE_USER', 'GEODATA'),
        'database': f"{os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE_NAME')}",
        'categories': {}
    }
    
    for category_group, results in all_results.items():
        summary['categories'][category_group] = {}
        total_objects = 0
        
        for subcategory, df in results.items():
            count = len(df)
            summary['categories'][category_group][subcategory] = count
            total_objects += count
        
        summary['categories'][category_group]['total'] = total_objects
    
    return summary

def save_results_to_files(all_results: Dict[str, Dict[str, pd.DataFrame]], summary: Dict[str, Any]):
    """Salva resultados em arquivos"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"oracle_objects_{timestamp}"
    
    # Salvar resumo em JSON
    summary_file = f"{base_filename}_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"📄 Resumo salvo em: {summary_file}")
    
    # Salvar dados detalhados em CSV
    csv_files = []
    for category_group, results in all_results.items():
        for subcategory, df in results.items():
            if not df.empty:
                csv_file = f"{base_filename}_{category_group}_{subcategory}.csv"
                df.to_csv(csv_file, index=False, encoding='utf-8')
                csv_files.append(csv_file)
    
    print(f"📊 {len(csv_files)} arquivos CSV criados:")
    for csv_file in csv_files:
        print(f"   • {csv_file}")
    
    # Salvar relatório consolidado em texto
    report_file = f"{base_filename}_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("RELATÓRIO DE OBJETOS ORACLE ACESSÍVEIS\n")
        f.write("="*80 + "\n")
        f.write(f"Usuário: {summary['user']}\n")
        f.write(f"Banco: {summary['database']}\n")
        f.write(f"Data/Hora: {summary['execution_time']}\n")
        f.write("\n")
        
        for category_group, results in all_results.items():
            f.write(f"\n{category_group.upper().replace('_', ' ')}\n")
            f.write("-" * 40 + "\n")
            
            for subcategory, df in results.items():
                if not df.empty:
                    f.write(f"\n{subcategory.replace('_', ' ').title()}: {len(df)} objetos\n")
                    
                    # Listar primeiros 10 objetos
                    for i, row in df.head(10).iterrows():
                        if 'OWNER' in row and pd.notna(row['OWNER']):
                            f.write(f"   • {row['OWNER']}.{row['OBJECT_NAME']} ({row['OBJECT_TYPE']})\n")
                        else:
                            f.write(f"   • {row['OBJECT_NAME']} ({row['OBJECT_TYPE']})\n")
                    
                    if len(df) > 10:
                        f.write(f"   ... e mais {len(df) - 10} objetos\n")
        
        f.write(f"\n\nRESUMO GERAL\n")
        f.write("-" * 20 + "\n")
        for category_group, cat_summary in summary['categories'].items():
            f.write(f"{category_group.replace('_', ' ').title()}: {cat_summary['total']} objetos\n")
    
    print(f"📋 Relatório consolidado salvo em: {report_file}")

def print_summary_console(summary: Dict[str, Any]):
    """Exibe resumo no console"""
    print("\n" + "="*80)
    print("📊 RESUMO GERAL")
    print("="*80)
    print(f"👤 Usuário: {summary['user']}")
    print(f"🗄️  Banco: {summary['database']}")
    print(f"⏰ Data/Hora: {summary['execution_time']}")
    print()
    
    total_general = 0
    for category_group, cat_summary in summary['categories'].items():
        print(f"📁 {category_group.replace('_', ' ').title()}: {cat_summary['total']} objetos")
        for subcategory, count in cat_summary.items():
            if subcategory != 'total' and count > 0:
                print(f"   • {subcategory.replace('_', ' ').title()}: {count}")
        total_general += cat_summary['total']
        print()
    
    print(f"🎯 TOTAL GERAL: {total_general} objetos acessíveis")

def main():
    """Função principal"""
    print("🚀 LISTAGEM DE OBJETOS ORACLE ACESSÍVEIS - ETL GEODATA")
    print("=" * 80)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Conectar ao Oracle
    connection = get_oracle_connection()
    if not connection:
        print("💥 Falha na conexão. Verifique as credenciais no arquivo .env")
        return
    
    try:
        # Coletar dados
        all_results = {}
        
        # Objetos próprios do usuário
        all_results['owned_objects'] = get_user_owned_objects(connection)
        
        # Objetos acessíveis de outros schemas
        all_results['accessible_objects'] = get_accessible_objects(connection)
        
        # Privilégios do usuário
        all_results['user_privileges'] = get_user_privileges(connection)
        
        # Gerar resumo
        summary = generate_summary(all_results)
        
        # Exibir resumo no console
        print_summary_console(summary)
        
        # Salvar arquivos
        print("\n" + "="*80)
        print("💾 SALVANDO RESULTADOS")
        print("="*80)
        save_results_to_files(all_results, summary)
        
        print(f"\n🎉 Análise concluída com sucesso!")
        
    except Exception as e:
        print(f"💥 Erro durante a execução: {e}")
        
    finally:
        # Fechar conexão
        connection.close()
        print("🔐 Conexão Oracle fechada")

if __name__ == "__main__":
    main()