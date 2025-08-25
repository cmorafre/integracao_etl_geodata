#!/usr/bin/env python3
"""
Arquivo para testar conexões com Oracle e PostgreSQL
Execute este arquivo antes do ETL principal para validar as conexões
"""

import cx_Oracle
import psycopg2
import pandas as pd
from datetime import datetime
import sys

def test_oracle_connection():
    """Testa conexão com Oracle"""
    print("=" * 60)
    print("TESTANDO CONEXÃO COM ORACLE")
    print("=" * 60)
    
    try:
        # Configurações Oracle
        oracle_host = "192.168.10.243"
        oracle_port = 1521
        oracle_service = "ORCL"
        oracle_user = "GEODATA"
        oracle_password = "GEo,D4tA0525#!"
        
        # String de conexão
        dsn = cx_Oracle.makedsn(oracle_host, oracle_port, service_name=oracle_service)
        print(f"📡 Tentando conectar em: {oracle_host}:{oracle_port}/{oracle_service}")
        print(f"👤 Usuário: {oracle_user}")
        
        # Conectar
        connection = cx_Oracle.connect(user=oracle_user, password=oracle_password, dsn=dsn)
        cursor = connection.cursor()
        
        # Teste básico
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        print(f"✅ Conexão Oracle OK!")
        print(f"🕐 Data/hora do servidor: {result[0]}")
        
        # Teste de schema
        cursor.execute("SELECT COUNT(*) FROM USER_TABLES")
        table_count = cursor.fetchone()[0]
        print(f"📊 Tabelas disponíveis no schema GEODATA: {table_count}")
        
        # Listar algumas tabelas
        cursor.execute("SELECT TABLE_NAME FROM USER_TABLES WHERE ROWNUM <= 5")
        tables = cursor.fetchall()
        print("📋 Primeiras 5 tabelas:")
        for table in tables:
            print(f"   • {table[0]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO na conexão Oracle: {e}")
        return False

def test_postgresql_connection():
    """Testa conexão com PostgreSQL"""
    print("\n" + "=" * 60)
    print("TESTANDO CONEXÃO COM POSTGRESQL")
    print("=" * 60)
    
    try:
        # Configurações PostgreSQL
        pg_host = "localhost"
        pg_port = 5432
        pg_database = "postgres"
        pg_user = "postgres"
        pg_password = "geo@2025!@"
        
        print(f"📡 Tentando conectar em: {pg_host}:{pg_port}/{pg_database}")
        print(f"👤 Usuário: {pg_user}")
        
        # Conectar
        connection = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password
        )
        
        cursor = connection.cursor()
        
        # Teste básico
        cursor.execute("SELECT NOW()")
        result = cursor.fetchone()
        print(f"✅ Conexão PostgreSQL OK!")
        print(f"🕐 Data/hora do servidor: {result[0]}")
        
        # Teste de versão
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"🐘 Versão PostgreSQL: {version.split(',')[0]}")
        
        # Teste de permissões - criar tabela teste
        test_table_sql = """
        CREATE TABLE IF NOT EXISTS teste_etl (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100),
            data_teste TIMESTAMP DEFAULT NOW()
        )
        """
        cursor.execute(test_table_sql)
        
        # Inserir dados teste
        cursor.execute("INSERT INTO teste_etl (nome) VALUES ('Teste ETL')")
        
        # Verificar inserção
        cursor.execute("SELECT COUNT(*) FROM teste_etl")
        count = cursor.fetchone()[0]
        print(f"📝 Teste de escrita OK - Registros na tabela teste: {count}")
        
        # Limpar teste
        cursor.execute("DROP TABLE teste_etl")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO na conexão PostgreSQL: {e}")
        return False

def test_pandas_integration():
    """Testa integração com pandas"""
    print("\n" + "=" * 60)
    print("TESTANDO INTEGRAÇÃO COM PANDAS")
    print("=" * 60)
    
    try:
        # Teste Oracle com pandas
        oracle_dsn = cx_Oracle.makedsn("192.168.10.243", 1521, service_name="ORCL")
        oracle_conn_str = f"oracle+cx_oracle://GEODATA:GEo,D4tA0525#!@{oracle_dsn}"
        
        df_oracle = pd.read_sql("SELECT SYSDATE as data_atual FROM DUAL", oracle_conn_str)
        print(f"✅ Pandas + Oracle OK! Data: {df_oracle.iloc[0]['data_atual']}")
        
        # Teste PostgreSQL com pandas
        pg_conn_str = "postgresql://postgres:geo@2025!@@localhost:5432/postgres"
        df_pg = pd.read_sql("SELECT NOW() as data_atual", pg_conn_str)
        print(f"✅ Pandas + PostgreSQL OK! Data: {df_pg.iloc[0]['data_atual']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO na integração Pandas: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DE CONEXÃO ETL GEODATA")
    print(f"⏰ Data/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    oracle_ok = test_oracle_connection()
    pg_ok = test_postgresql_connection()
    pandas_ok = test_pandas_integration()
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    print(f"Oracle Connection:     {'✅ OK' if oracle_ok else '❌ FALHOU'}")
    print(f"PostgreSQL Connection: {'✅ OK' if pg_ok else '❌ FALHOU'}")
    print(f"Pandas Integration:    {'✅ OK' if pandas_ok else '❌ FALHOU'}")
    
    if oracle_ok and pg_ok and pandas_ok:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para ETL.")
        sys.exit(0)
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM! Verifique as conexões antes de executar o ETL.")
        sys.exit(1)

if __name__ == "__main__":
    main()
