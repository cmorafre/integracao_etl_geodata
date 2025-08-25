# 🚀 ETL GEODATA - Guia de Instalação Completo

Este guia detalha como instalar e configurar o sistema ETL GEODATA para migração de dados Oracle → PostgreSQL no Ubuntu Server.

## 📋 Pré-requisitos

- **Sistema Operacional**: Ubuntu 18.04+
- **Python**: 3.8+
- **Memória RAM**: Mínimo 2GB (recomendado 4GB+)
- **Espaço em Disco**: Mínimo 1GB livre
- **Acesso de rede**: Oracle (192.168.10.243:1521) e PostgreSQL (localhost:5432)
- **Usuário**: Privilégios sudo para instalação

## 🏗️ Estrutura do Projeto

```
/opt/etl_geodata/
├── main.py                 # Script principal
├── config.py              # Configurações
├── etl_functions.py       # Funções ETL
├── test_connections.py    # Teste de conexões
├── requirements.txt       # Dependências Python
├── setup.sh              # Script de instalação
├── etl_cron.sh           # Script para cron
├── logs/                 # Diretório de logs
├── backup/               # Backups (se necessário)
├── temp/                 # Arquivos temporários
├── sql_scripts/          # Scripts SQL (link simbólico)
└── venv/                 # Ambiente virtual Python
```

## 🔧 Instalação Automática (Recomendada)

### 1. Download dos Arquivos

```bash
# Criar diretório temporário
mkdir -p ~/etl_geodata_temp
cd ~/etl_geodata_temp

# Copie todos os arquivos Python (.py) para este diretório
# main.py, config.py, etl_functions.py, test_connections.py, etc.
```

### 2. Executar Setup Automático

```bash
# Dar permissão de execução
chmod +x setup.sh

# Executar instalação
./setup.sh
```

O script irá:
- ✅ Verificar sistema e Python
- ✅ Instalar dependências Ubuntu
- ⚠️ Orientar instalação Oracle Client (manual)
- ✅ Criar ambiente virtual Python
- ✅ Instalar pacotes Python
- ✅ Criar estrutura de diretórios
- ✅ Configurar scripts de cron
- ✅ Configurar logrotate

### 3. Instalação Manual Oracle Instant Client

⚠️ **IMPORTANTE**: O Oracle Client precisa ser instalado manualmente:

```bash
# 1. Baixar do site Oracle (requer conta gratuita):
# https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html

# 2. Baixar ambos os arquivos:
# - instantclient-basic-linux.x64-21.1.0.0.0.zip
# - instantclient-sqlplus-linux.x64-21.1.0.0.0.zip

# 3. Instalar
sudo mkdir -p /opt/oracle
sudo unzip instantclient-basic-linux.x64-21.1.0.0.0.zip -d /opt/oracle/
sudo unzip instantclient-sqlplus-linux.x64-21.1.0.0.0.zip -d /opt/oracle/

# 4. Configurar variáveis de ambiente
echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH' >> ~/.bashrc
echo 'export PATH=/opt/oracle/instantclient_21_1:$PATH' >> ~/.bashrc
source ~/.bashrc

# 5. Testar
sqlplus -v
```

## 🔧 Instalação Manual (Passo a Passo)

Se preferir instalar manualmente:

### 1. Dependências do Sistema

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev libpq-dev libaio1 cron
```

### 2. Criar Estrutura

```bash
sudo mkdir -p /opt/etl_geodata
sudo chown $USER:$USER /opt/etl_geodata
cd /opt/etl_geodata
mkdir -p logs backup temp
```

### 3. Ambiente Virtual Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 4. Instalar Dependências Python

```bash
pip install pandas>=1.5.0
pip install cx_Oracle>=8.3.0
pip install psycopg2-binary>=2.9.0
pip install SQLAlchemy>=1.4.0
pip install python-dateutil>=2.8.0
```

### 5. Copiar Arquivos Python

```bash
# Copie todos os arquivos .py para /opt/etl_geodata/
cp ~/etl_geodata_temp/*.py .
```

## ⚙️ Configuração

### 1. Ajustar Caminhos

Edite o arquivo `config.py` e ajuste:

```python
# Caminho para seus scripts SQL
SQL_SCRIPTS_DIR = "/Users/cmorafre/Development/scripts_geodata"

# Ou crie um link simbólico:
# sudo ln -s /Users/cmorafre/Development/scripts_geodata /opt/etl_geodata/sql_scripts
# SQL_SCRIPTS_DIR = "/opt/etl_geodata/sql_scripts"
```

### 2. Validar Credenciais

As credenciais já estão configuradas em `config.py`:
- **Oracle**: 192.168.10.243:1521/ORCL (GEODATA)
- **PostgreSQL**: localhost:5432/postgres (postgres)

## 🧪 Testes

### 1. Teste de Conectividade

```bash
cd /opt/etl_geodata
source venv/bin/activate
python test_connections.py
```

**Saída esperada:**
```
✅ Conexão Oracle OK!
✅ Conexão PostgreSQL OK!  
✅ Pandas + Oracle OK!
✅ Pandas + PostgreSQL OK!
🎉 TODOS OS TESTES PASSARAM! Sistema pronto para ETL.
```

### 2. Validação Dry Run

```bash
python main.py --dry-run
```

### 3. Teste com Arquivo Específico

```bash
python main.py --file nome_do_arquivo.sql
```

### 4. Execução Completa (Teste)

```bash
python main.py
```

## ⏰ Agendamento (Cron)

### 1. Configurar Execução Diária

```bash
crontab -e
```

Adicionar linha:
```bash
# ETL GEODATA - Execução diária às 02:00
0 2 * * * /opt/etl_geodata/etl_cron.sh
```

### 2. Verificar Agendamento

```bash
crontab -l
```

### 3. Monitorar Logs do Cron

```bash
tail -f /opt/etl_geodata/logs/cron.log
tail -f /opt/etl_geodata/logs/etl_geodata.log
```

## 📊 Monitoramento

### 1. Logs Principais

- **ETL Principal**: `/opt/etl_geodata/logs/etl_geodata.log`
- **Cron**: `/opt/etl_geodata/logs/cron.log`
- **Histórico Cron**: `/opt/etl_geodata/logs/cron_history.log`

### 2. Comandos Úteis

```bash
# Ver últimas execuções
tail -f /opt/etl_geodata/logs/etl_geodata.log

# Ver estatísticas
grep "RELATÓRIO FINAL" /opt/etl_geodata/logs/etl_geodata.log

# Ver erros
grep "ERROR\|❌" /opt/etl_geodata/logs/etl_geodata.log

# Limpar logs antigos
find /opt/etl_geodata/logs -name "*.log*" -mtime +30 -delete
```

## 🚨 Solução de Problemas

### Erro: "Oracle Client não encontrado"

```bash
# Verificar instalação
echo $LD_LIBRARY_PATH
ls /opt/oracle/instantclient_21_1/

# Reconfigurar
export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1:$LD_LIBRARY_PATH
```

### Erro: "Permission denied" no PostgreSQL

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão manual
psql -h localhost -U postgres -d postgres
```

### Erro: "cx_Oracle.DatabaseError"

```bash
# Verificar conectividade Oracle
telnet 192.168.10.243 1521

# Testar com sqlplus
sqlplus GEODATA/GEo,D4tA0525#!@192.168.10.243:1521/ORCL
```

### Erro: "Arquivo SQL não encontrado"

```bash
# Verificar caminho
ls -la /Users/cmorafre/Development/scripts_geodata/

# Ajustar permissões se necessário
chmod +r /Users/cmorafre/Development/scripts_geodata/*.sql
```

### Performance Lenta

```bash
# Ajustar batch size em config.py
ETL_CONFIG = {
    'batch_size': 500,  # Reduzir se necessário
}

# Monitorar recursos
htop
iostat -x 1
```

## 📈 Manutenção

### 1. Backup de Configurações

```bash
# Backup semanal
tar -czf backup/etl_config_$(date +%Y%m%d).tar.gz *.py
```

### 2. Atualização de Dependências

```bash
cd /opt/etl_geodata
source venv/bin/activate
pip list --outdated
pip install --upgrade package_name
```

### 3. Limpeza Regular

```bash
# Limpar logs antigos (automático via logrotate)
sudo logrotate /etc/logrotate.d/etl-geodata

# Limpar temp
rm -rf /opt/etl_geodata/temp/*
```

## 🔐 Segurança

### 1. Permissões de Arquivo

```bash
chmod 600 config.py  # Proteger credenciais
chmod +x main.py etl_cron.sh
```

### 2. Logs Sensíveis

```bash
# Os logs não devem conter senhas
grep -i "password\|senha" /opt/etl_geodata/logs/*.log
```

## ✅ Checklist Final

- [ ] Sistema Ubuntu atualizado
- [ ] Python 3.8+ instalado
- [ ] Oracle Instant Client configurado
- [ ] Ambiente virtual criado
- [ ] Dependências Python instaladas
- [ ] Arquivos Python copiados
- [ ] Configurações ajustadas
- [ ] Teste de conexão passou
- [ ] Dry run executado
- [ ] Cron configurado
- [ ] Logs funcionando
- [ ] Monitoramento ativo

---

## 📞 Suporte

Para problemas ou dúvidas:

1. **Verificar logs**: `/opt/etl_geodata/logs/etl_geodata.log`
2. **Executar dry run**: `python main.py --dry-run`
3. **Testar conexões**: `python test_connections.py`
4. **Validar configuração**: `python config.py`

**Sistema pronto para produção! 🚀**