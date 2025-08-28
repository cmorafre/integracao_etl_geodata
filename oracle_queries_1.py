#!/usr/bin/env python3
"""
Script para testar queries Oracle específicas
Conecta no banco Oracle usando as configurações do .env e testa arquivos SQL individualmente
"""


import os
import sys
import cx_Oracle
import logging
from pathlib import Path
from datetime import datetime
import traceback

# Adicionar o diretório do projeto ao path para importar módulos locais
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ORACLE_CONFIG, get_oracle_connection_string, 
    SQL_SCRIPTS_DIR, LOG_CONFIG
)

def setup_logging():
    """Configura logging para o script de teste"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def test_oracle_connection():
    """Testa conexão básica com Oracle"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔍 Testando conexão Oracle...")
        
        # Criar conexão usando cx_Oracle diretamente
        dsn = cx_Oracle.makedsn(
            ORACLE_CONFIG['host'],
            ORACLE_CONFIG['port'],
            service_name=ORACLE_CONFIG['service_name']
        )
        
        connection = cx_Oracle.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=dsn,
            encoding=ORACLE_CONFIG['encoding']
        )
        
        # Teste básico
        cursor = connection.cursor()
        cursor.execute("SELECT SYSDATE, USER, SYS_CONTEXT('USERENV','DB_NAME') FROM DUAL")
        result = cursor.fetchone()
        
        logger.info(f"✅ Conexão Oracle OK!")
        logger.info(f"📅 Data/Hora do servidor: {result[0]}")
        logger.info(f"👤 Usuário conectado: {result[1]}")
        logger.info(f"🗄️  Banco de dados: {result[2]}")
        
        cursor.close()
        connection.close()
        
        return True, None
        
    except Exception as e:
        logger.error(f"❌ Erro na conexão Oracle: {e}")
        return False, str(e)

def clean_sql_content(sql_content):
    """Remove comentários e comandos problemáticos do SQL"""
    import re
    
    # Remover comentários de linha única
    sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    
    # Remover comentários de bloco
    sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
    
    # Remover comandos Oracle específicos
    oracle_commands = [
        r'SET\s+\w+.*?;',
        r'WHENEVER\s+.*?;',
        r'SPOOL\s+.*?;',
        r'PROMPT\s+.*?;'
    ]
    
    for cmd in oracle_commands:
        sql_content = re.sub(cmd, '', sql_content, flags=re.IGNORECASE)
    
    # Remover múltiplas quebras de linha
    sql_content = re.sub(r'\n\s*\n', '\n', sql_content)
    
    return sql_content.strip()

def test_sql_file(sql_file_path):
    """Testa um arquivo SQL específico no Oracle"""
    logger = logging.getLogger(__name__)
    
    try:
        sql_file = Path(sql_file_path)
        if not sql_file.exists():
            return False, f"Arquivo não encontrado: {sql_file_path}"
        
        logger.info(f"🧪 Testando arquivo: {sql_file.name}")
        
        # Ler conteúdo do arquivo
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read().strip()
        
        if not sql_content:
            return False, "Arquivo SQL vazio"
        
        # Limpar SQL
        sql_content = clean_sql_content(sql_content)
        
        if not sql_content:
            return False, "Arquivo SQL vazio após limpeza"
        
        # Conectar ao Oracle
        dsn = cx_Oracle.makedsn(
            ORACLE_CONFIG['host'],
            ORACLE_CONFIG['port'],
            service_name=ORACLE_CONFIG['service_name']
        )
        
        connection = cx_Oracle.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=dsn,
            encoding=ORACLE_CONFIG['encoding']
        )
        
        cursor = connection.cursor()
        
        # Executar query com LIMIT para teste
        test_query = f"""
        SELECT * FROM (
            {sql_content}
        ) WHERE ROWNUM <= 5
        """
        
        logger.info("⏳ Executando query de teste (LIMIT 5)...")
        start_time = datetime.now()
        
        cursor.execute(test_query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Query executada com sucesso!")
        logger.info(f"📊 Colunas retornadas: {len(columns)}")
        logger.info(f"📋 Registros teste: {len(results)}")
        logger.info(f"⏱️  Tempo execução: {execution_time:.2f}s")
        
        # Mostrar algumas informações das colunas
        logger.info("📋 Primeiras colunas:")
        for i, col in enumerate(columns[:10]):  # Primeiras 10 colunas
            logger.info(f"   {i+1}. {col}")
        
        if len(columns) > 10:
            logger.info(f"   ... e mais {len(columns)-10} colunas")
        
        cursor.close()
        connection.close()
        
        return True, {
            'columns': len(columns),
            'column_names': columns,
            'test_records': len(results),
            'execution_time': execution_time
        }
        
    except cx_Oracle.DatabaseError as e:
        error_obj, = e.args
        logger.error(f"❌ Erro Oracle: {error_obj.code} - {error_obj.message}")
        return False, f"Oracle Error {error_obj.code}: {error_obj.message}"
        
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        return False, str(e)

def explain_plan_query(sql_file_path):
    """Executa EXPLAIN PLAN para analisar performance"""
    logger = logging.getLogger(__name__)
    
    try:
        sql_file = Path(sql_file_path)
        logger.info(f"📊 Analisando plano de execução: {sql_file.name}")
        
        # Ler e limpar SQL
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = clean_sql_content(f.read().strip())
        
        # Conectar ao Oracle
        dsn = cx_Oracle.makedsn(
            ORACLE_CONFIG['host'],
            ORACLE_CONFIG['port'],
            service_name=ORACLE_CONFIG['service_name']
        )
        
        connection = cx_Oracle.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=dsn,
            encoding=ORACLE_CONFIG['encoding']
        )
        
        cursor = connection.cursor()
        
        # Executar EXPLAIN PLAN
        explain_query = f"EXPLAIN PLAN FOR {sql_content}"
        cursor.execute(explain_query)
        
        # Buscar plano de execução
        plan_query = """
        SELECT LPAD(' ', 2*LEVEL) || OPERATION || ' ' || OPTIONS || ' ' || OBJECT_NAME AS "Execution Plan",
               COST, CARDINALITY
        FROM PLAN_TABLE
        CONNECT BY PRIOR ID = PARENT_ID
        START WITH ID = 0
        ORDER BY ID
        """
        
        cursor.execute(plan_query)
        plan_results = cursor.fetchall()
        
        logger.info("📊 Plano de execução:")
        for row in plan_results:
            plan_step = row[0] if row[0] else "Unknown"
            cost = row[1] if row[1] else "N/A"
            cardinality = row[2] if row[2] else "N/A"
            logger.info(f"   {plan_step} (Cost: {cost}, Rows: {cardinality})")
        
        # Limpar tabela de plano
        cursor.execute("DELETE FROM PLAN_TABLE")
        
        cursor.close()
        connection.close()
        
        return True, len(plan_results)
        
    except Exception as e:
        logger.warning(f"⚠️  Não foi possível gerar plano de execução: {e}")
        return False, str(e)

def main():
    """Função principal"""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("🧪 TESTE DE QUERIES ORACLE - ETL GEODATA")
    logger.info("=" * 80)
    logger.info(f"📅 Teste iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Testar conexão básica
    connection_ok, connection_error = test_oracle_connection()
    if not connection_ok:
        logger.error("💥 Falha na conexão. Abortando testes.")
        sys.exit(1)
    
    # 2. Arquivos SQL para testar
    sql_files_to_test = [
        "carteira_pedido_venda_erp.sql",
        "faturamento_erp.sql"
    ]
    
    results = {}
    
    for sql_file in sql_files_to_test:
        logger.info("\n" + "=" * 60)
        
        # Definir caminho completo do arquivo
        if os.path.exists(Path(SQL_SCRIPTS_DIR) / sql_file):
            sql_file_path = Path(SQL_SCRIPTS_DIR) / sql_file
        else:
            # Tentar na pasta sqls do projeto atual
            sql_file_path = Path("sqls") / sql_file
        
        if not sql_file_path.exists():
            logger.error(f"❌ Arquivo não encontrado: {sql_file}")
            results[sql_file] = {"success": False, "error": "Arquivo não encontrado"}
            continue
        
        # Testar query
        success, result = test_sql_file(sql_file_path)
        results[sql_file] = {"success": success, "result": result}
        
        if success:
            # Tentar analisar plano de execução
            explain_success, explain_result = explain_plan_query(sql_file_path)
            results[sql_file]["explain_plan"] = {"success": explain_success, "result": explain_result}
    
    # 3. Relatório final
    logger.info("\n" + "=" * 80)
    logger.info("📋 RELATÓRIO FINAL DOS TESTES")
    logger.info("=" * 80)
    
    successful_tests = 0
    failed_tests = 0
    
    for sql_file, result in results.items():
        if result["success"]:
            logger.info(f"✅ {sql_file}: OK")
            if isinstance(result["result"], dict):
                logger.info(f"   📊 Colunas: {result['result']['columns']}")
                logger.info(f"   ⏱️  Tempo: {result['result']['execution_time']:.2f}s")
            successful_tests += 1
        else:
            logger.error(f"❌ {sql_file}: ERRO")
            logger.error(f"   🔍 Detalhes: {result['result']}")
            failed_tests += 1
    
    logger.info(f"\n📊 Resumo: {successful_tests} sucessos, {failed_tests} falhas")
    logger.info(f"⏱️  Teste finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed_tests > 0:
        logger.info("\n💡 SUGESTÕES PARA CORREÇÃO:")
        logger.info("1. Verificar se todas as tabelas existem no banco")
        logger.info("2. Verificar permissões do usuário Oracle")
        logger.info("3. Verificar sintaxe SQL específica do Oracle")
        logger.info("4. Verificar se funções customizadas existem (ex: custo_medio)")
        sys.exit(1)
    else:
        logger.info("\n🎉 Todos os testes passaram com sucesso!")
        sys.exit(0)

if __name__ == "__main__":
    main()