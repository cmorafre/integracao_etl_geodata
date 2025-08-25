# ETL GEODATA - Guia de Deploy

## Instalação no Servidor Ubuntu

### Pré-requisitos
- Ubuntu 18.04+ 
- Usuário com privilégios sudo
- Conectividade com Oracle (192.168.10.243:1521) e PostgreSQL (localhost:5432)

### Passos de Instalação

1. **Clone o repositório no servidor Ubuntu:**
```bash
cd ~/
git clone <url-do-seu-repositorio> integracao_etl_geodata
cd integracao_etl_geodata
```

2. **Execute o setup automatizado:**
```bash
chmod +x setup.sh
./setup.sh
```

O script fará automaticamente:
- ✅ Instalação do Oracle Instant Client
- ✅ Criação do ambiente Python em `/opt/etl_geodata/`
- ✅ Cópia de todos os arquivos Python e SQL
- ✅ Configuração do ambiente virtual
- ✅ Instalação das dependências Python
- ✅ Configuração dos logs e cron

3. **Teste a instalação:**
```bash
cd /opt/etl_geodata
source venv/bin/activate
python test_connections.py
```

### Estrutura Final no Servidor

```
/opt/etl_geodata/
├── main.py                 # Script principal
├── config.py              # Configurações (sem credenciais hardcoded)
├── .env                   # Credenciais (criado automaticamente, permissões 600)
├── etl_functions.py       # Funções ETL
├── test_connections.py    # Teste de conexões
├── requirements.txt       # Dependências Python
├── etl_cron.sh           # Script para cron
├── venv/                 # Ambiente virtual Python
├── logs/                 # Diretório de logs
├── backup/               # Backups de configuração
├── temp/                 # Arquivos temporários
└── sql_scripts/          # Arquivos SQL (copiados automaticamente)
    ├── clientes_erp.sql
    ├── produtos_erp.sql
    ├── faturamento_erp.sql
    └── ... (todos os arquivos .sql)
```

### 🔒 Segurança Aprimorada

**Credenciais Protegidas:**
- ✅ Sem senhas no código fonte
- ✅ Arquivo `.env` com permissões restritas (600)
- ✅ Configurações específicas por ambiente
- ✅ Validação automática de credenciais obrigatórias

### Comandos Úteis Pós-Instalação

```bash
# Ativar ambiente virtual
cd /opt/etl_geodata && source venv/bin/activate

# Testar conexões
python test_connections.py

# Testar um arquivo específico
python main.py --file clientes_erp.sql

# Executar ETL completo
python main.py

# Ver logs em tempo real
tail -f logs/etl_geodata.log

# Configurar cron para execução diária às 2:00
crontab -e
# Adicionar: 0 2 * * * /opt/etl_geodata/etl_cron.sh
```

### Troubleshooting

**Oracle Client não funciona:**
```bash
# Verificar se está instalado
sqlplus -v

# Verificar variáveis de ambiente
echo $LD_LIBRARY_PATH
echo $ORACLE_HOME

# Recarregar configurações
source ~/.bashrc
```

**Problemas com PostgreSQL:**
```bash
# Verificar se está rodando
sudo systemctl status postgresql

# Testar conexão manual
psql -h localhost -U postgres -d postgres
```

**Arquivos SQL não encontrados:**
- Os arquivos são copiados automaticamente da pasta `sqls/` do projeto
- Se necessário, copie manualmente: `cp /caminho/dos/sqls/*.sql /opt/etl_geodata/sql_scripts/`