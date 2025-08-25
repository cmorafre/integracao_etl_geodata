# Guia de Segurança - ETL GEODATA

## 🔒 Gerenciamento Seguro de Credenciais

### Problema Anterior
❌ Credenciais hardcoded no arquivo `config.py`
❌ Senhas visíveis no código fonte
❌ Riscos de exposição no repositório público

### Solução Implementada
✅ Credenciais em variáveis de ambiente
✅ Arquivo `.env` para configuração local
✅ `.gitignore` protege arquivos sensíveis
✅ Validação de configurações obrigatórias

## 📁 Estrutura de Segurança

```
projeto/
├── .env                    # ❌ NUNCA committar - credenciais reais
├── .env.example           # ✅ Template público seguro
├── .gitignore             # ✅ Proteção de arquivos sensíveis
├── config.py              # ✅ Sem credenciais hardcoded
└── SECURITY.md            # ✅ Este arquivo
```

## 🚀 Configuração para Diferentes Ambientes

### Desenvolvimento Local
```bash
# 1. Clone o repositório
git clone <repo> etl_geodata
cd etl_geodata

# 2. Configure ambiente local
chmod +x setup_local.sh
./setup_local.sh

# 3. O arquivo .env será criado automaticamente
```

### Produção (Servidor Ubuntu)
```bash
# 1. Clone o repositório
git clone <repo> integracao_etl_geodata
cd integracao_etl_geodata

# 2. Execute setup de produção
chmod +x setup.sh
./setup.sh

# 3. O arquivo .env será criado em /opt/etl_geodata/.env
```

### Configuração Manual (Alternativa)
```bash
# 1. Copie o template
cp .env.example .env

# 2. Edite com suas credenciais reais
nano .env

# 3. Configure permissões restritivas
chmod 600 .env
```

## 🛡️ Boas Práticas de Segurança

### ✅ O que FAZER:
- Usar variáveis de ambiente para credenciais
- Manter arquivo `.env` com permissões 600 (somente dono lê/escreve)
- Usar credenciais diferentes para cada ambiente
- Fazer backup seguro das configurações de produção
- Rotacionar senhas regularmente

### ❌ O que NÃO fazer:
- ❌ Commitar arquivos `.env` no Git
- ❌ Compartilhar credenciais por email/chat
- ❌ Usar mesma senha em desenvolvimento e produção
- ❌ Deixar arquivo `.env` com permissões abertas
- ❌ Hardcodar senhas no código

## 🔐 Variáveis de Ambiente Suportadas

### Oracle Database
```bash
ORACLE_HOST=192.168.10.243
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCL
ORACLE_USER=geodata_user
ORACLE_PASSWORD=senha_segura
```

### PostgreSQL Database  
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=geodata
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=senha_segura
```

### Configurações ETL
```bash
ETL_LOAD_STRATEGY=replace
ETL_QUERY_TIMEOUT=300
ETL_BATCH_SIZE=1000
ETL_LOG_LEVEL=INFO
```

### Diretórios
```bash
SQL_SCRIPTS_PATH=/opt/etl_geodata/sql_scripts
LOG_DIRECTORY=/opt/etl_geodata/logs
```

## 🚨 Recuperação de Emergência

### Se credenciais forem comprometidas:
1. **Pare imediatamente** todos os processos ETL
2. **Altere as senhas** nos bancos de dados
3. **Atualize o arquivo .env** com novas credenciais
4. **Reinicie os serviços** ETL
5. **Revise logs** para atividade suspeita

### Se arquivo .env for perdido:
1. Use o backup seguro das configurações
2. Ou reconfigure usando `.env.example` como template
3. Teste conexões com `python test_connections.py`

## 🔍 Monitoramento de Segurança

### Verificações Regulares:
```bash
# Verificar permissões do .env
ls -la .env
# Deve mostrar: -rw------- (600)

# Testar configurações
python config.py

# Verificar se não há credenciais no Git
git log -p | grep -i password
```

### Logs de Segurança:
- Monitore falhas de autenticação
- Verifique tentativas de conexão suspeitas
- Acompanhe mudanças em configurações

## ⚡ Solução de Problemas

### Erro: "Configurações Oracle obrigatórias não definidas"
```bash
# Verificar se arquivo .env existe e tem as variáveis corretas
cat .env | grep ORACLE

# Testar carregamento
python -c "from config import ORACLE_CONFIG; print(ORACLE_CONFIG)"
```

### Erro: "Arquivo .env não encontrado"
```bash
# Criar arquivo .env a partir do template
cp .env.example .env

# Editar com credenciais reais
nano .env
```

### Permissões incorretas:
```bash
# Corrigir permissões
chmod 600 .env
chown $USER:$USER .env
```

---

**🚨 LEMBRE-SE: Segurança é responsabilidade de todos!**

Mantenha suas credenciais seguras e nunca as compartilhe em canais inseguros.