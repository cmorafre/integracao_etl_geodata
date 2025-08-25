#!/usr/bin/env python3
"""
ETL GEODATA - Script Principal
Executa o processo completo de ETL Oracle -> PostgreSQL
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import signal
from pathlib import Path

# Imports locais
from config import (
    SQL_SCRIPTS_DIR, LOG_CONFIG, validate_config
)
from etl_functions import (
    ETLProcessor, cleanup_old_logs, send_notification, 
    create_summary_report, dry_run_validation
)

def setup_logging():
    """Configura sistema de logging"""
    # Criar logger principal
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_CONFIG['level']))
    
    # Limpar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formatter
    formatter = logging.Formatter(
        LOG_CONFIG['format'],
        datefmt=LOG_CONFIG['date_format']
    )
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        LOG_CONFIG['log_file'],
        maxBytes=LOG_CONFIG['max_file_size'],
        backupCount=LOG_CONFIG['backup_count'],
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def signal_handler(signum, frame):
    """Handler para sinais de interrupção"""
    logger = logging.getLogger(__name__)
    logger.warning(f"🛑 Recebido sinal {signum}. Finalizando processo ETL...")
    sys.exit(1)

def validate_environment():
    """Valida ambiente e configurações"""
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 Validando ambiente...")
    
    # Validar configurações
    config_errors = validate_config()
    if config_errors:
        logger.error("❌ Erros de configuração encontrados:")
        for error in config_errors:
            logger.error(f"   • {error}")
        return False
    
    # Validar dependências Python
    required_packages = [
        'pandas', 'cx_Oracle', 'psycopg2', 'sqlalchemy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ Pacotes Python faltando: {', '.join(missing_packages)}")
        logger.error("💡 Execute: pip install -r requirements.txt")
        return False
    
    logger.info("✅ Ambiente validado com sucesso")
    return True

def main():
    """Função principal"""
    # Configurar logging
    logger = setup_logging()
    
    # Configurar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Cabeçalho
    logger.info("=" * 80)
    logger.info("🚀 ETL GEODATA - ORACLE → POSTGRESQL")
    logger.info("=" * 80)
    logger.info(f"📅 Execução iniciada em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📁 Diretório SQL: {SQL_SCRIPTS_DIR}")
    logger.info(f"📝 Log: {LOG_CONFIG['log_file']}")
    
    try:
        # 1. Validar ambiente
        if not validate_environment():
            logger.error("💥 Falha na validação do ambiente")
            sys.exit(1)
        
        # 2. Limpeza de logs antigos
        cleanup_old_logs(LOG_CONFIG['log_file'].parent)
        
        # 3. Validação dry run (opcional - para verificar arquivos)
        logger.info("🧪 Executando validação prévia dos arquivos SQL...")
        validation_result = dry_run_validation(SQL_SCRIPTS_DIR)
        
        if validation_result['valid_files'] == 0:
            logger.error("❌ Nenhum arquivo SQL válido encontrado!")
            sys.exit(1)
        
        if validation_result['invalid_files']:
            logger.warning(f"⚠️  {len(validation_result['invalid_files'])} arquivos com problemas serão ignorados:")
            for invalid in validation_result['invalid_files'][:5]:  # Mostrar apenas os primeiros 5
                logger.warning(f"   • {invalid['file']}: {invalid['message']}")
        
        logger.info(f"✅ {validation_result['valid_files']} arquivos válidos prontos para processamento")
        
        # 4. Executar ETL
        logger.info("🎯 Iniciando processamento ETL...")
        
        etl_processor = ETLProcessor()
        result = etl_processor.process_all_files(SQL_SCRIPTS_DIR)
        
        # 5. Análise dos resultados
        if result['success']:
            logger.info("🎉 ETL concluído COM SUCESSO!")
            
            # Notificação de sucesso
            message = f"ETL GEODATA executado com sucesso! {result['processed_files']} arquivos processados, {result['total_records']:,} registros carregados."
            send_notification(message, "SUCCESS")
            
            sys.exit(0)
            
        else:
            logger.error("💥 ETL concluído COM ERROS!")
            
            # Detalhes do erro
            if 'error' in result:
                logger.error(f"Erro principal: {result['error']}")
            
            logger.error(f"📊 Arquivos processados: {result.get('processed_files', 0)}")
            logger.error(f"📊 Total de registros: {result.get('total_records', 0):,}")
            logger.error(f"❌ Erros: {result.get('errors', 0)}")
            
            # Notificação de erro
            error_msg = result.get('error', 'Erros durante processamento')
            message = f"ETL GEODATA falhou! Erro: {error_msg}. {result.get('errors', 0)} erros encontrados."
            send_notification(message, "ERROR")
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("🛑 Processo interrompido pelo usuário")
        send_notification("ETL GEODATA interrompido pelo usuário", "WARNING")
        sys.exit(130)  # Código padrão para Ctrl+C
        
    except Exception as e:
        logger.error(f"💥 ERRO CRÍTICO NÃO TRATADO: {e}", exc_info=True)
        send_notification(f"ETL GEODATA erro crítico: {e}", "CRITICAL")
        sys.exit(1)
        
    finally:
        logger.info("🔐 Finalizando ETL GEODATA")
        logger.info(f"⏱️  Execução finalizada em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def run_test_mode():
    """Executa modo de teste com um arquivo específico"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETL GEODATA - Modo Teste')
    parser.add_argument('--file', '-f', required=True, help='Arquivo SQL específico para testar')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Apenas validar sem processar')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    if args.dry_run:
        logger.info("🧪 MODO DRY RUN - Apenas validação")
        validation = dry_run_validation(SQL_SCRIPTS_DIR)
        
        print("\n📋 RESULTADO DA VALIDAÇÃO:")
        print(f"Total de arquivos: {validation['total_files']}")
        print(f"Arquivos válidos: {validation['valid_files']}")
        
        if validation['invalid_files']:
            print(f"Arquivos inválidos: {len(validation['invalid_files'])}")
            for invalid in validation['invalid_files']:
                print(f"  • {invalid['file']}: {invalid['message']}")
        
        return
    
    # Teste de arquivo específico
    from etl_functions import test_single_sql_file
    
    sql_file_path = Path(SQL_SCRIPTS_DIR) / args.file
    if not sql_file_path.exists():
        logger.error(f"❌ Arquivo não encontrado: {sql_file_path}")
        sys.exit(1)
    
    logger.info(f"🧪 MODO TESTE - Processando: {args.file}")
    
    result = test_single_sql_file(str(sql_file_path))
    
    if result['success']:
        logger.info("✅ Teste concluído com sucesso!")
        print(f"📊 Estatísticas: {result['stats']}")
    else:
        logger.error(f"❌ Teste falhou: {result.get('error', 'Erro desconhecido')}")
        sys.exit(1)

if __name__ == "__main__":
    # Verificar se foi chamado com argumentos de teste
    if len(sys.argv) > 1 and ('--file' in sys.argv or '--dry-run' in sys.argv):
        run_test_mode()
    else:
        main()
