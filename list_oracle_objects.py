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

def get_bentivi_objects(engine) -> Dict[str, pd.DataFrame]:
    """Obtém objetos do schema BENTIVI que o usuário GEODATA pode acessar"""
    queries = {
        'tables': {
            'query': """
                SELECT 
                    TABLE_NAME,
                    'TABLE' as OBJECT_TYPE,
                    NVL(NUM_ROWS, 0) as NUM_ROWS,
                    TO_CHAR(LAST_ANALYZED, 'YYYY-MM-DD') as LAST_ANALYZED,
                    TABLESPACE_NAME,
                    STATUS
                FROM ALL_TABLES 
                WHERE OWNER = 'BENTIVI'
                ORDER BY TABLE_NAME
            """,
            'description': 'Tabelas do schema BENTIVI'
        },
        'views': {
            'query': """
                SELECT 
                    VIEW_NAME as TABLE_NAME,
                    'VIEW' as OBJECT_TYPE,
                    TEXT_LENGTH,
                    READ_ONLY,
                    'N/A' as STATUS
                FROM ALL_VIEWS 
                WHERE OWNER = 'BENTIVI'
                ORDER BY VIEW_NAME
            """,
            'description': 'Views do schema BENTIVI'
        },
        'procedures': {
            'query': """
                SELECT 
                    OBJECT_NAME as TABLE_NAME,
                    OBJECT_TYPE,
                    STATUS,
                    TO_CHAR(CREATED, 'YYYY-MM-DD') as CREATED,
                    TO_CHAR(LAST_DDL_TIME, 'YYYY-MM-DD') as LAST_DDL_TIME
                FROM ALL_OBJECTS 
                WHERE OWNER = 'BENTIVI' 
                AND OBJECT_TYPE IN ('PROCEDURE', 'PACKAGE', 'PACKAGE BODY')
                ORDER BY OBJECT_TYPE, OBJECT_NAME
            """,
            'description': 'Procedures e Packages do schema BENTIVI'
        },
        'functions': {
            'query': """
                SELECT 
                    OBJECT_NAME as TABLE_NAME,
                    OBJECT_TYPE,
                    STATUS,
                    TO_CHAR(CREATED, 'YYYY-MM-DD') as CREATED,
                    TO_CHAR(LAST_DDL_TIME, 'YYYY-MM-DD') as LAST_DDL_TIME
                FROM ALL_OBJECTS 
                WHERE OWNER = 'BENTIVI' 
                AND OBJECT_TYPE = 'FUNCTION'
                ORDER BY OBJECT_NAME
            """,
            'description': 'Functions do schema BENTIVI'
        }
    }
    
    print("\n" + "="*60)
    print("📋 OBJETOS DO SCHEMA BENTIVI ACESSÍVEIS PELO USUÁRIO GEODATA")
    print("="*60)
    
    results = {}
    for category, info in queries.items():
        df = execute_query_to_dataframe(engine, info['query'], info['description'])
        results[category] = df
    
    return results

def get_bentivi_privileges(engine) -> Dict[str, pd.DataFrame]:
    """Obtém privilégios específicos do usuário GEODATA no schema BENTIVI"""
    queries = {
        'table_privileges': {
            'query': """
                SELECT 
                    TABLE_NAME,
                    'PRIVILEGE' as OBJECT_TYPE,
                    PRIVILEGE,
                    GRANTABLE,
                    GRANTOR
                FROM USER_TAB_PRIVS 
                WHERE OWNER = 'BENTIVI'
                ORDER BY TABLE_NAME, PRIVILEGE
            """,
            'description': 'Privilégios em objetos do schema BENTIVI'
        }
    }
    
    print("\n" + "="*60)
    print("🔐 PRIVILÉGIOS NO SCHEMA BENTIVI")
    print("="*60)
    
    results = {}
    for category, info in queries.items():
        df = execute_query_to_dataframe(engine, info['query'], info['description'])
        results[category] = df
    
    return results

# Função removida - focando apenas no schema BENTIVI

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

def save_bentivi_report(all_results: Dict[str, Dict[str, pd.DataFrame]], summary: Dict[str, Any]):
    """Salva relatório focado no schema BENTIVI"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"bentivi_objects_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        # Cabeçalho
        f.write("="*80 + "\n")
        f.write("RELATÓRIO DE OBJETOS DO SCHEMA BENTIVI\n")
        f.write("="*80 + "\n")
        f.write(f"Usuário GEODATA - Acesso ao Schema: BENTIVI\n")
        f.write(f"Banco: {summary['database']}\n")
        f.write(f"Data/Hora: {summary['execution_time']}\n")
        f.write("="*80 + "\n\n")
        
        # Resumo geral
        f.write("📊 RESUMO GERAL - SCHEMA BENTIVI\n")
        f.write("-" * 50 + "\n")
        total_general = 0
        for category_group, cat_summary in summary['categories'].items():
            total_general += cat_summary['total']
            for subcategory, count in cat_summary.items():
                if subcategory != 'total' and count > 0:
                    f.write(f"• {subcategory.replace('_', ' ').title()}: {count} objetos\n")
        
        f.write(f"\n🎯 TOTAL DE OBJETOS BENTIVI ACESSÍVEIS: {total_general}\n")
        f.write("\n" + "="*80 + "\n\n")
        
        # Detalhes por categoria
        for category_group, results in all_results.items():
            for subcategory, df in results.items():
                if not df.empty:
                    f.write(f"📋 {subcategory.replace('_', ' ').upper()} DO SCHEMA BENTIVI\n")
                    f.write("="*80 + "\n")
                    
                    # Listar todos os objetos
                    for i, row in df.iterrows():
                        # Usar TABLE_NAME que é a coluna padrão que definimos
                        object_name = row.get('TABLE_NAME', 'NOME_NAO_ENCONTRADO')
                        object_type = row.get('OBJECT_TYPE', 'TIPO_DESCONHECIDO')
                        
                        line = f"{i+1:4d}. BENTIVI.{object_name} ({object_type})"
                        
                        # Informações extras
                        extra_info = []
                        if 'STATUS' in row and pd.notna(row['STATUS']) and str(row['STATUS']).upper() != 'N/A':
                            extra_info.append(f"Status: {row['STATUS']}")
                        if 'NUM_ROWS' in row and pd.notna(row['NUM_ROWS']) and row['NUM_ROWS'] > 0:
                            extra_info.append(f"Registros: {row['NUM_ROWS']:,}")
                        if 'LAST_ANALYZED' in row and pd.notna(row['LAST_ANALYZED']) and str(row['LAST_ANALYZED']) != 'None':
                            extra_info.append(f"Analisada: {row['LAST_ANALYZED']}")
                        if 'CREATED' in row and pd.notna(row['CREATED']) and str(row['CREATED']) != 'None':
                            extra_info.append(f"Criada: {row['CREATED']}")
                        if 'TABLESPACE_NAME' in row and pd.notna(row['TABLESPACE_NAME']):
                            extra_info.append(f"Tablespace: {row['TABLESPACE_NAME']}")
                        if 'TEXT_LENGTH' in row and pd.notna(row['TEXT_LENGTH']):
                            extra_info.append(f"Tamanho: {row['TEXT_LENGTH']} chars")
                        if 'READ_ONLY' in row and pd.notna(row['READ_ONLY']):
                            extra_info.append(f"Somente Leitura: {row['READ_ONLY']}")
                        if 'PRIVILEGE' in row and pd.notna(row['PRIVILEGE']):
                            extra_info.append(f"Privilégio: {row['PRIVILEGE']}")
                        if 'GRANTABLE' in row and pd.notna(row['GRANTABLE']) and str(row['GRANTABLE']).upper() == 'YES':
                            extra_info.append("Pode conceder")
                        
                        if extra_info:
                            line += f"\n     [{', '.join(extra_info)}]"
                        
                        f.write(line + "\n")
                    
                    f.write(f"\n   TOTAL: {len(df)} {subcategory.replace('_', ' ')} encontradas\n")
                    f.write("\n" + "="*80 + "\n\n")
        
        # Se não encontrou nenhum objeto
        if total_general == 0:
            f.write("⚠️  ATENÇÃO: Nenhum objeto encontrado no schema BENTIVI\n")
            f.write("   Possíveis causas:\n")
            f.write("   • Schema BENTIVI não existe\n")
            f.write("   • Usuário GEODATA não tem privilégios de acesso\n")
            f.write("   • Schema está vazio\n\n")
        
        # Rodapé
        f.write("INFORMAÇÕES ADICIONAIS\n")
        f.write("-" * 40 + "\n")
        f.write("• Este relatório mostra APENAS objetos do schema BENTIVI\n")
        f.write("• Tipos de objeto: TABELAS, VIEWS, PROCEDURES, FUNCTIONS\n")
        f.write("• Usuário consultado: GEODATA\n")
        f.write("• Schema consultado: BENTIVI\n")
        f.write(f"• Relatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n" + "="*80 + "\n")
    
    print(f"📋 Relatório do schema BENTIVI salvo em: {report_file}")
    print(f"📄 Total de objetos encontrados: {total_general}")
    return report_file

def print_bentivi_summary(summary: Dict[str, Any]):
    """Exibe resumo focado no schema BENTIVI"""
    print("\n" + "="*80)
    print("📊 RESUMO - SCHEMA BENTIVI")
    print("="*80)
    print(f"👤 Usuário: GEODATA")
    print(f"🗄️  Schema: BENTIVI")
    print(f"🗄️  Banco: {summary['database']}")
    print(f"⏰ Data/Hora: {summary['execution_time']}")
    print()
    
    total_general = 0
    for category_group, cat_summary in summary['categories'].items():
        for subcategory, count in cat_summary.items():
            if subcategory != 'total' and count > 0:
                print(f"📁 {subcategory.replace('_', ' ').title()}: {count} objetos")
                total_general += count
    
    print()
    if total_general > 0:
        print(f"🎯 TOTAL DE OBJETOS BENTIVI ACESSÍVEIS: {total_general}")
    else:
        print("⚠️  Nenhum objeto encontrado no schema BENTIVI")
        print("   Verifique se o schema existe e se há privilégios de acesso")

def main():
    """Função principal - foco no schema BENTIVI"""
    print("🚀 ANÁLISE DE OBJETOS DO SCHEMA BENTIVI")
    print("=" * 80)
    print(f"👤 Usuário: GEODATA")
    print(f"🗄️  Schema: BENTIVI") 
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Conectar ao Oracle
    engine = get_oracle_engine()
    if not engine:
        print("💥 Falha na conexão. Verifique as credenciais no arquivo .env")
        return
    
    try:
        # Coletar dados apenas do schema BENTIVI
        all_results = {}
        
        # Objetos do schema BENTIVI
        all_results['bentivi_objects'] = get_bentivi_objects(engine)
        
        # Privilégios específicos no schema BENTIVI
        all_results['bentivi_privileges'] = get_bentivi_privileges(engine)
        
        # Gerar resumo
        summary = generate_summary(all_results)
        
        # Exibir resumo no console
        print_bentivi_summary(summary)
        
        # Salvar arquivo
        print("\n" + "="*80)
        print("💾 SALVANDO RELATÓRIO DO SCHEMA BENTIVI")
        print("="*80)
        report_file = save_bentivi_report(all_results, summary)
        
        print(f"\n🎉 Análise do schema BENTIVI concluída!")
        
    except Exception as e:
        print(f"💥 Erro durante a execução: {e}")
        
    finally:
        # Fechar engine
        engine.dispose()
        print("🔐 Conexão Oracle fechada")

if __name__ == "__main__":
    main()