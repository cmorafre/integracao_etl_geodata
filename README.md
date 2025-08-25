# ETL GEODATA - Oracle → PostgreSQL

Sistema de ETL (Extract, Transform, Load) para migração de dados geodésicos do Oracle para PostgreSQL com execução automatizada e monitoramento completo.

## 📋 Sumário

- [Requisitos](#requisitos)
- [Instalação Rápida](#instalação-rápida)
- [Instalação Detalhada](#instalação-detalhada)
- [Configuração de Credenciais](#configuração-de-credenciais)
- [Agendamento Automático](#agendamento-automático)
- [Execução Manual](#execução-manual)
- [Monitoramento e Logs](#monitoramento-e-logs)
- [Solução de Problemas](#solução-de-problemas)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Comandos Úteis](#comandos-úteis)

## 🔧 Requisitos

### Sistema Operacional
- **Ubuntu 18.04+** (recomendado)
- Outras distribuições Linux (instalação manual)

### Software
- **Python 3.8+**
- **Oracle Instant Client** (instalado automaticamente)
- **PostgreSQL Client** (psycopg2)
- **Sudo/Root access** (apenas durante instalação)

### Bancos de Dados
- **Oracle Database** (origem dos dados)
- **PostgreSQL Database** (destino dos dados)

## 🚀 Instalação Rápida

```bash
# 1. Clonar repositório
git clone <repo-url> integracao_etl_geodata
cd integracao_etl_geodata

# 2. Executar instalação completa
chmod +x setup.sh
./setup.sh

# 3. Configurar credenciais
cd /opt/etl_geodata
./configure_credentials.sh

# 4. Testar sistema
python test_connections.py
python main.py --dry-run
```

## 📚 Instalação Detalhada

### Fase 1: Infraestrutura

```bash
# Preparação
git clone <repo-url> integracao_etl_geodata
cd integracao_etl_geodata

# Executar setup (instala tudo automaticamente)
chmod +x setup.sh
./setup.sh
```

**O que o setup.sh faz:**
- ✅ Verifica sistema Ubuntu e Python 3.8+
- ✅ Instala dependências do sistema (libpq-dev, libaio1, etc.)
- ✅ Baixa e configura Oracle Instant Client automaticamente
- ✅ Cria ambiente virtual Python em `/opt/etl_geodata/venv`
- ✅ Instala pacotes Python (pandas, cx_Oracle, psycopg2, etc.)
- ✅ Cria estrutura de diretórios (logs, backup, temp, sql_scripts)
- ✅ Configura logrotate para gerenciamento de logs
- ✅ Cria script de agendamento (`etl_cron.sh`)
- ✅ Copia arquivos do projeto para `/opt/etl_geodata/`

### Fase 2: Credenciais

```bash
# Navegar para diretório do projeto
cd /opt/etl_geodata

# Configurar credenciais interativamente
./configure_credentials.sh
```

**O que o configure_credentials.sh faz:**
- 🔒 Coleta credenciais Oracle e PostgreSQL de forma segura
- 🧪 Testa conexões antes de salvar
- 📝 Cria arquivo `.env` com permissões 600
- ✅ Valida configurações finais

## 🔐 Configuração de Credenciais

### Credenciais Necessárias

**Oracle Database (Origem):**
- Host/IP do servidor
- Porta (padrão: 1521)
- Service Name
- Usuário
- Senha

**PostgreSQL Database (Destino):**
- Host/IP do servidor
- Porta (padrão: 5432)
- Nome do database
- Usuário
- Senha

### Processo Interativo

```bash
./configure_credentials.sh
```

**Exemplo de execução:**
```
🔒 CONFIGURAÇÃO DE CREDENCIAIS
==================================

🚀 COMO USAR:
   1. Para cada pergunta, você verá um valor padrão em [amarelo]
   2. Pressione ENTER para aceitar o padrão
   3. Ou digite um novo valor para substituir
   4. As senhas ficarão ocultas quando digitadas

📊 CONFIGURAÇÕES ORACLE (Banco de Origem)
═══════════════════════════════════════════
Host/IP do servidor Oracle [192.168.10.243]: 
Porta do Oracle [1521]: 
Service Name [ORCL]: 
Usuário Oracle [GEODATA]: 
Senha Oracle: ********

🧪 Testando conexão Oracle...
✅ Conexão Oracle OK!
📅 Data/hora do servidor: 2024-08-25 10:30:45

🐘 CONFIGURAÇÕES POSTGRESQL (Banco de Destino)
═══════════════════════════════════════════════
Host/IP do servidor PostgreSQL [localhost]: 
Porta do PostgreSQL [5432]: 
Nome do database [postgres]: 
Usuário PostgreSQL [postgres]: 
Senha PostgreSQL: ********

🧪 Testando conexão PostgreSQL...
✅ Conexão PostgreSQL OK!
📅 Data/hora do servidor: 2024-08-25 10:30:47

📝 Criando arquivo de configuração .env...
✅ Arquivo .env criado com sucesso!
🔒 Permissões restritivas aplicadas (600)

🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!
```

### Configuração Manual (Alternativa)

```bash
# Copiar template
cp .env.example .env

# Editar arquivo
nano .env

# Aplicar permissões restritivas
chmod 600 .env
```

## ⏰ Agendamento Automático

### Como Funciona

O sistema usa **cron** (agendador Linux) + **etl_cron.sh** (script wrapper):

```
Cron → etl_cron.sh → main.py → Logs
```

### Configurar Agendamento

```bash
# 1. Testar script wrapper
cd /opt/etl_geodata
./etl_cron.sh

# 2. Verificar logs do teste
tail -f logs/cron.log
tail -f logs/etl_geodata.log

# 3. Configurar cron
crontab -e

# 4. Adicionar linha de agendamento (escolha uma):
0 2 * * *     /opt/etl_geodata/etl_cron.sh    # Diariamente às 02:00
0 */6 * * *   /opt/etl_geodata/etl_cron.sh    # A cada 6 horas  
30 1 * * 1    /opt/etl_geodata/etl_cron.sh    # Segundas às 01:30
0 0 1 * *     /opt/etl_geodata/etl_cron.sh    # 1º dia do mês à meia-noite

# 5. Salvar e sair (Ctrl+X → Y → Enter no nano)
```

### Verificar Agendamento

```bash
# Ver agendamentos ativos
crontab -l

# Testar cron manualmente
sudo service cron restart
sudo service cron status
```

### Formatos de Agendamento Cron

```bash
# Formato: minuto hora dia mês dia_semana comando
#          ┌─── minuto (0-59)
#          │ ┌─── hora (0-23)
#          │ │ ┌─── dia do mês (1-31)
#          │ │ │ ┌─── mês (1-12)
#          │ │ │ │ ┌─── dia da semana (0-7, 0/7 = domingo)
#          │ │ │ │ │
#          * * * * *  comando

# Exemplos práticos:
0 2 * * *      # Todo dia às 02:00
0 */4 * * *    # A cada 4 horas
30 8 * * 1-5   # Dias úteis às 08:30
0 0 1 * *      # Todo dia 1º do mês à meia-noite
0 6 * * 0      # Domingos às 06:00
```

## ▶️ Execução Manual

### Teste de Conexões

```bash
cd /opt/etl_geodata
source venv/bin/activate
python test_connections.py
```

### Validação Prévia (Dry Run)

```bash
# Validar arquivos SQL sem executar
python main.py --dry-run
```

### Testar Arquivo Específico

```bash
# Processar apenas um arquivo SQL
python main.py --file nome_do_arquivo.sql
```

### Execução Completa

```bash
# Executar ETL completo
python main.py
```

### Execução com Logs Detalhados

```bash
# Ver logs em tempo real
python main.py & tail -f logs/etl_geodata.log
```

## 📊 Monitoramento e Logs

### Arquivos de Log

```bash
# Log principal do ETL
tail -f logs/etl_geodata.log

# Log das execuções via cron
tail -f logs/cron.log

# Histórico de execuções
tail -f logs/cron_history.log
```

### Monitoramento em Tempo Real

```bash
# Acompanhar execução atual
watch -n 2 "tail -10 /opt/etl_geodata/logs/etl_geodata.log"

# Ver estatísticas do sistema
htop

# Verificar uso de disco
df -h /opt/etl_geodata/
```

### Rotação de Logs

O sistema usa **logrotate** configurado automaticamente:
- 📅 Rotação diária
- 📦 Compressão automática  
- 🗄️ Mantém 30 dias de histórico
- 🧹 Remove logs vazios automaticamente

### Localização dos Logs

```bash
/opt/etl_geodata/logs/
├── etl_geodata.log         # Log principal (atual)
├── etl_geodata.log.1       # Log do dia anterior
├── etl_geodata.log.2.gz    # Logs mais antigos (comprimidos)
├── cron.log                # Saída das execuções via cron
└── cron_history.log        # Histórico simples de execuções
```

## 🔧 Solução de Problemas

### Erro: "Módulo cx_Oracle não encontrado"

```bash
# Verificar ambiente virtual
cd /opt/etl_geodata
source venv/bin/activate
pip list | grep cx-Oracle

# Reinstalar se necessário
pip install cx_Oracle>=8.3.0

# Verificar Oracle Client
export LD_LIBRARY_PATH="/opt/oracle/instantclient_19_1:$LD_LIBRARY_PATH"
python -c "import cx_Oracle; print('OK')"
```

### Erro: "Arquivo .env não encontrado"

```bash
# Executar configuração de credenciais
cd /opt/etl_geodata
./configure_credentials.sh

# Ou criar manualmente
cp .env.example .env
nano .env
chmod 600 .env
```

### Erro: "Falha na conexão Oracle"

```bash
# Testar Oracle Client
/opt/oracle/instantclient_19_1/sqlplus -v

# Verificar variáveis de ambiente
echo $ORACLE_HOME
echo $LD_LIBRARY_PATH

# Reconfigurar se necessário
source ~/.bashrc
```

### Erro: "Permission denied" no cron

```bash
# Verificar permissões do script
chmod +x /opt/etl_geodata/etl_cron.sh

# Verificar propriedade dos arquivos
sudo chown -R $USER:$USER /opt/etl_geodata/
```

### Logs não aparecem no cron

```bash
# Verificar se cron está rodando
sudo service cron status

# Verificar logs do sistema cron
sudo tail -f /var/log/cron

# Testar script manualmente
/opt/etl_geodata/etl_cron.sh
```

### ETL travando ou ficando lento

```bash
# Verificar processos Python rodando
ps aux | grep python

# Monitorar recursos
htop

# Verificar locks no banco
# (consultas específicas para Oracle/PostgreSQL)

# Ajustar configurações no .env
nano .env
# ETL_BATCH_SIZE=500  (reduzir se necessário)
# ETL_QUERY_TIMEOUT=600  (aumentar se necessário)
```

## 📁 Estrutura do Projeto

```
/opt/etl_geodata/
├── main.py                     # Script principal do ETL
├── config.py                   # Configurações e validações
├── etl_functions.py            # Funções do ETL
├── test_connections.py         # Teste de conexões
├── configure_credentials.sh    # Configuração interativa
├── configure_credentials_simple.sh  # Versão sem testes
├── etl_cron.sh                # Script para cron
├── .env                       # Credenciais (criado após config)
├── .env.backup               # Backup automático do .env
├── requirements.txt          # Dependências Python
├── venv/                     # Ambiente virtual Python
├── logs/                     # Todos os arquivos de log
│   ├── etl_geodata.log
│   ├── cron.log
│   └── cron_history.log
├── backup/                   # Backups de dados
├── temp/                     # Arquivos temporários
└── sql_scripts/             # Scripts SQL para ETL
    ├── tabela1.sql
    ├── tabela2.sql
    └── ...
```

## 🛠️ Comandos Úteis

### Navegação e Ativação

```bash
# Ir para diretório do projeto
cd /opt/etl_geodata

# Ativar ambiente virtual
source venv/bin/activate

# Desativar ambiente virtual
deactivate
```

### Execução e Teste

```bash
# Teste de conexões
python test_connections.py

# ETL completo
python main.py

# Modo dry-run (apenas validação)
python main.py --dry-run

# Processar arquivo específico
python main.py --file arquivo.sql

# Executar via wrapper (como no cron)
./etl_cron.sh
```

### Monitoramento

```bash
# Logs em tempo real
tail -f logs/etl_geodata.log

# Últimas 50 linhas do log
tail -50 logs/etl_geodata.log

# Buscar erros nos logs
grep -i error logs/etl_geodata.log

# Ver execuções do cron
tail -f logs/cron_history.log

# Estatísticas de arquivos
ls -la sql_scripts/
wc -l sql_scripts/*.sql
```

### Gerenciamento

```bash
# Ver agendamentos cron
crontab -l

# Editar agendamentos
crontab -e

# Reconfigurar credenciais
./configure_credentials.sh

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Verificar espaço em disco
df -h /opt/etl_geodata/
du -sh /opt/etl_geodata/logs/
```

### Backup e Manutenção

```bash
# Backup das configurações
cp .env .env.backup.$(date +%Y%m%d)

# Limpar logs antigos manualmente
find logs/ -name "*.log.*" -mtime +30 -delete

# Verificar integridade do sistema
python -c "from config import validate_config; print('Erros:', validate_config())"

# Restart completo do cron
sudo service cron restart
```

## 📞 Suporte

### Logs para Análise
Quando reportar problemas, inclua:

```bash
# Informações do sistema
cat /etc/os-release
python3 --version
/opt/oracle/instantclient_19_1/sqlplus -v

# Status do ambiente
cd /opt/etl_geodata
python -c "from config import validate_config; print(validate_config())"

# Últimos logs
tail -100 logs/etl_geodata.log
```

### Arquivos Importantes
- `logs/etl_geodata.log` - Log principal
- `.env` - Configurações (⚠️ **remover senhas** antes de compartilhar)
- `crontab -l` - Agendamentos ativos

---

## 🔒 Segurança

⚠️ **IMPORTANTE:** 
- Nunca compartilhe o arquivo `.env` (contém senhas)
- Mantenha permissões 600 no arquivo `.env`
- Use usuários de banco com privilégios mínimos necessários
- Monitore logs regularmente para atividades suspeitas

Para mais detalhes de segurança, consulte: [`SECURITY.md`](SECURITY.md)

---

**🚀 Sistema ETL GEODATA - Pronto para Produção!**