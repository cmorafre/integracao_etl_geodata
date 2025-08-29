#!/usr/bin/env python3
"""
Script para adicionar schema BENTIVI. em todas as tabelas do SQL
"""

import re
import sys

def add_bentivi_schema(sql_content):
    """
    Adiciona o schema BENTIVI. antes de todas as referências de tabelas Oracle
    """
    
    # Lista de todas as tabelas identificadas no script original
    tables = [
        'estoque', 'topctrl', 'receber', 'cabrec', 'notacrc', 'INOTA', 'NOTA', 
        'CICLO', 'CABTAB', 'TRANSAC', 'PROPRIED', 'MUNICIPIO', 'PESSOAL', 
        'FUNCAOTOPER', 'TIPOOPER', 'CFO', 'PRODSERV', 'GRUPO', 'SUBGRUPO', 
        'PRODUTO', 'transac', 'condicao', 'indexador', 'INDVALOR', 'inota', 
        'nota', 'notaorig', 'INFENTRA', 'NOTAORIG', 'pedido', 'ipedido', 
        'CULTURA', 'receita', 'ireceita', 'NFENTRA', 'IDOCDESFAZ', 'DOCDESFAZ', 
        'CABDESFAZ'
    ]
    
    # Remove duplicatas e ordena por tamanho (maiores primeiro para evitar substituições parciais)
    unique_tables = sorted(set(tables), key=len, reverse=True)
    
    print(f"Processando {len(unique_tables)} tabelas únicas...")
    
    # Para cada tabela, adiciona BENTIVI. se não estiver presente
    for table in unique_tables:
        # Padrões para capturar diferentes contextos onde a tabela aparece
        patterns = [
            # FROM, JOIN patterns
            rf'\b(FROM|JOIN|INNER JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN)\s+{table}\b',
            # Patterns específicos para subqueries
            rf'\bFROM\s+{table}\s+',
            rf'\bJOIN\s+{table}\s+',
        ]
        
        for pattern in patterns:
            # Substitui apenas se BENTIVI. não estiver presente
            replacement_pattern = rf'\1 BENTIVI.{table}'
            if 'FROM' in pattern or 'JOIN' in pattern:
                sql_content = re.sub(
                    rf'(?<!BENTIVI\.)\b(FROM|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|JOIN)\s+{re.escape(table)}\b',
                    rf'\1 BENTIVI.{table}',
                    sql_content,
                    flags=re.IGNORECASE
                )
    
    return sql_content

def main():
    input_file = '/Users/cmorafre/Development/projects/integracao_etl_geodata/sqls/faturamento_erp_v2_otimizado_v2.sql'
    output_file = '/Users/cmorafre/Development/projects/integracao_etl_geodata/sqls/faturamento_erp_v2_final.sql'
    
    try:
        print(f"Lendo arquivo: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Aplicando schema BENTIVI...")
        updated_content = add_bentivi_schema(content)
        
        print(f"Salvando arquivo: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ Script concluído com sucesso!")
        print(f"📁 Arquivo final salvo em: {output_file}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()