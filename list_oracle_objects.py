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
from sqlalchemy import create_engine, text

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

def get_oracle_engine():
    """Cria engine SQLAlchemy para Oracle usando credenciais do .env"""
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
        
        # Criar string de conexão SQLAlchemy
        dsn = cx_Oracle.makedsn(oracle_host, oracle_port, service_name=oracle_service)
        connection_string = f"oracle+cx_oracle://{oracle_user}:{oracle_password}@{dsn}"
        
        # Criar engine
        engine = create_engine(
            connection_string,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Testar conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM DUAL"))
        
        print("✅ Conexão Oracle estabelecida com sucesso!")
        return engine
        
    except Exception as e:
        print(f"❌ Erro ao conectar no Oracle: {e}")
        return None

def execute_query_to_dataframe(engine, query: str, description: str) -> pd.DataFrame:
    """Executa query e retorna DataFrame"""
    try:
        print(f"🔍 Executando consulta: {description}")
        df = pd.read_sql(query, engine)
        print(f"   📊 {len(df)} registros encontrados")
        return df
    except Exception as e:
        print(f"   ❌ Erro na consulta {description}: {e}")
        return pd.DataFrame()

def get_user_owned_objects(engine) -> Dict[str, pd.DataFrame]:
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
        df = execute_query_to_dataframe(engine, info['query'], info['description'])
        results[category] = df
    
    return results

def get_accessible_objects(engine) -> Dict[str, pd.DataFrame]:
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
        df = execute_query_to_dataframe(engine, info['query'], info['description'])
        results[category] = df
    
    return results

def get_user_privileges(engine) -> Dict[str, pd.DataFrame]:
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
        df = execute_query_to_dataframe(engine, info['query'], info['description'])
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

def save_results_to_file(all_results: Dict[str, Dict[str, pd.DataFrame]], summary: Dict[str, Any]):
    """Salva todos os resultados em um único arquivo TXT detalhado"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"oracle_objects_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        # Cabeçalho
        f.write("="*80 + "\n")
        f.write("RELATÓRIO COMPLETO DE OBJETOS ORACLE ACESSÍVEIS\n")
        f.write("="*80 + "\n")
        f.write(f"Usuário: {summary['user']}\n")
        f.write(f"Banco: {summary['database']}\n")
        f.write(f"Data/Hora: {summary['execution_time']}\n")
        f.write("="*80 + "\n\n")
        
        # Resumo geral no topo
        f.write("📊 RESUMO GERAL\n")
        f.write("-" * 40 + "\n")
        total_general = 0
        for category_group, cat_summary in summary['categories'].items():
            f.write(f"• {category_group.replace('_', ' ').title()}: {cat_summary['total']} objetos\n")
            total_general += cat_summary['total']
        f.write(f"\n🎯 TOTAL GERAL: {total_general} objetos acessíveis\n")
        f.write("\n" + "="*80 + "\n\n")
        
        # Detalhes por categoria
        for category_group, results in all_results.items():
            f.write(f"📁 {category_group.upper().replace('_', ' ')}\n")
            f.write("="*80 + "\n")
            
            category_total = 0
            for subcategory, df in results.items():
                if not df.empty:
                    category_total += len(df)
                    f.write(f"\n📋 {subcategory.replace('_', ' ').title()}: {len(df)} objetos\n")
                    f.write("-" * 60 + "\n")
                    
                    # Listar TODOS os objetos (não apenas os primeiros 10)
                    for i, row in df.iterrows():
                        # Formatar linha baseado no tipo de informação disponível
                        if 'OWNER' in row and pd.notna(row['OWNER']) and row['OWNER'] != summary['user']:
                            # Objeto de outro schema
                            line = f"{i+1:4d}. {row['OWNER']}.{row['OBJECT_NAME']} ({row['OBJECT_TYPE']})"
                        else:
                            # Objeto próprio do usuário
                            line = f"{i+1:4d}. {row['OBJECT_NAME']} ({row['OBJECT_TYPE']})"
                        
                        # Adicionar informações extras se disponíveis
                        extra_info = []
                        if 'STATUS' in row and pd.notna(row['STATUS']):
                            extra_info.append(f"Status: {row['STATUS']}")
                        if 'NUM_ROWS' in row and pd.notna(row['NUM_ROWS']):
                            extra_info.append(f"Linhas: {row['NUM_ROWS']:,}")
                        if 'TABLE_NAME' in row and pd.notna(row['TABLE_NAME']) and row['OBJECT_TYPE'] in ['INDEX', 'CONSTRAINT']:
                            extra_info.append(f"Tabela: {row['TABLE_NAME']}")
                        if 'PRIVILEGE' in row and pd.notna(row['PRIVILEGE']):
                            extra_info.append(f"Privilégio: {row['PRIVILEGE']}")
                        if 'GRANTABLE' in row and pd.notna(row['GRANTABLE']) and row['GRANTABLE'] == 'YES':
                            extra_info.append("Pode conceder")
                        
                        if extra_info:
                            line += f" [{', '.join(extra_info)}]"
                        
                        f.write(line + "\n")
                    
                    f.write(f"\n   Total: {len(df)} objetos\n")
            
            if category_total == 0:
                f.write("   Nenhum objeto encontrado nesta categoria.\n")
            
            f.write(f"\n   SUBTOTAL {category_group.replace('_', ' ').upper()}: {category_total} objetos\n")
            f.write("\n" + "="*80 + "\n\n")
        
        # Rodapé
        f.write("INFORMAÇÕES ADICIONAIS\n")
        f.write("-" * 40 + "\n")
        f.write("• Este relatório lista todos os objetos Oracle acessíveis pelo usuário\n")
        f.write("• Objetos próprios não mostram o prefixo do schema (são do usuário atual)\n")
        f.write("• Objetos de outros schemas mostram SCHEMA.OBJETO\n")
        f.write("• Privilégios mostram o que o usuário pode fazer em cada objeto\n")
        f.write(f"• Gerado automaticamente em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n" + "="*80 + "\n")
    
    print(f"📋 Relatório completo salvo em: {report_file}")
    print(f"📄 Arquivo único contém {total_general} objetos detalhados")
    return report_file

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
    engine = get_oracle_engine()
    if not engine:
        print("💥 Falha na conexão. Verifique as credenciais no arquivo .env")
        return
    
    try:
        # Coletar dados
        all_results = {}
        
        # Objetos próprios do usuário
        all_results['owned_objects'] = get_user_owned_objects(engine)
        
        # Objetos acessíveis de outros schemas
        all_results['accessible_objects'] = get_accessible_objects(engine)
        
        # Privilégios do usuário
        all_results['user_privileges'] = get_user_privileges(engine)
        
        # Gerar resumo
        summary = generate_summary(all_results)
        
        # Exibir resumo no console
        print_summary_console(summary)
        
        # Salvar arquivo
        print("\n" + "="*80)
        print("💾 SALVANDO RELATÓRIO")
        print("="*80)
        report_file = save_results_to_file(all_results, summary)
        
        print(f"\n🎉 Análise concluída com sucesso!")
        
    except Exception as e:
        print(f"💥 Erro durante a execução: {e}")
        
    finally:
        # Fechar engine
        engine.dispose()
        print("🔐 Conexão Oracle fechada")

if __name__ == "__main__":
    main()