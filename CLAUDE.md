# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ETL (Extract, Transform, Load) system called **ETL GEODATA** that migrates data from Oracle to PostgreSQL. The system reads SQL files from a configured directory, executes them against an Oracle database, and loads the results into PostgreSQL tables.

## Architecture

The ETL system follows a modular architecture with the following key components:

- **main.py**: Entry point and orchestration layer. Handles argument parsing, logging setup, and process coordination
- **config.py**: Centralized configuration management for database connections, paths, and ETL parameters
- **etl_functions.py**: Core ETL processing logic with the `ETLProcessor` class that handles extract/transform/load operations
- **test_connections.py**: Standalone connection testing utility

### Key Design Patterns

- **Configuration-driven**: All settings centralized in `config.py` with validation
- **Pandas-based ETL**: Uses pandas DataFrames for data manipulation and SQLAlchemy for database operations
- **Schema inference**: Automatically infers PostgreSQL table schemas from pandas DataFrame types
- **Batch processing**: Configurable batch sizes for efficient data loading
- **Comprehensive logging**: Structured logging with rotation and different levels

## Development Commands

### Automated Setup (Recommended)
```bash
# Clone or extract project files
# Run automated setup (Ubuntu Server)
chmod +x setup.sh
./setup.sh
```

### Manual Environment Setup
```bash
# Create virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy SQL files to destination
cp sqls/*.sql /opt/etl_geodata/sql_scripts/
```

### Testing and Validation
```bash
# Test database connections
python test_connections.py

# Validate configuration
python config.py

# Dry run validation (check SQL files without processing)
python main.py --dry-run

# Test single SQL file
python main.py --file filename.sql
```

### Main ETL Execution
```bash
# Full ETL processing
python main.py

# Run from production environment
cd /opt/etl_geodata
source venv/bin/activate
python main.py
```

### Monitoring and Debugging
```bash
# View real-time logs
tail -f logs/etl_geodata.log

# Check cron execution logs
tail -f logs/cron.log

# View ETL statistics
grep "RELATÓRIO FINAL" logs/etl_geodata.log

# Check for errors
grep "ERROR\|❌" logs/etl_geodata.log
```

## Configuration Management

The system uses a centralized configuration approach in `config.py`:

- **SQL_SCRIPTS_DIR**: Path to directory containing SQL files to process
- **ORACLE_CONFIG**: Source database connection parameters
- **POSTGRESQL_CONFIG**: Destination database connection parameters  
- **ETL_CONFIG**: Processing parameters (batch size, load strategy, file patterns)
- **LOG_CONFIG**: Logging configuration with rotation

### Important Configuration Notes

- The system expects SQL files in the directory specified by `SQL_SCRIPTS_DIR`
- Database credentials are stored in plain text - ensure proper file permissions (600)
- Load strategy can be 'replace' (DROP/CREATE tables) or 'append'
- File patterns support regex for ignoring test/backup files

## Data Flow and Processing

1. **Discovery**: Scan `SQL_SCRIPTS_DIR` for `.sql` files (respecting ignore patterns)
2. **Validation**: Dry-run validation of SQL files before processing  
3. **Extract**: Execute SQL against Oracle database using pandas.read_sql()
4. **Transform**: Clean column names, infer PostgreSQL schema from DataFrame dtypes
5. **Load**: Create/replace PostgreSQL tables and insert data using pandas.to_sql()

### Schema Mapping

The system automatically maps Oracle data types to PostgreSQL equivalents:
- Uses `TYPE_MAPPING` for explicit Oracle->PostgreSQL type conversions
- Uses `PANDAS_TO_POSTGRESQL` for pandas dtype->PostgreSQL mappings
- Infers VARCHAR lengths based on actual data with safety margins

## Error Handling and Recovery

- Each SQL file is processed independently - failures don't stop the entire batch
- Comprehensive error logging with context information
- Transaction-based processing for data integrity
- Automatic cleanup of database connections
- Signal handling for graceful shutdown

## Production Deployment

The system is designed for Ubuntu Server deployment under `/opt/etl_geodata/`:

- Uses `setup.sh` for automated installation
- Includes cron script (`etl_cron.sh`) for scheduled execution
- Logrotate configuration for log management
- Virtual environment isolation

### Production Structure
```
/opt/etl_geodata/
├── main.py, config.py, etl_functions.py, test_connections.py
├── requirements.txt
├── setup.sh, etl_cron.sh  
├── venv/              # Python virtual environment
├── logs/              # ETL and cron logs
├── backup/            # Configuration backups
├── temp/              # Temporary processing files
└── sql_scripts/       # SQL files (automatically copied by setup.sh)
    ├── clientes_erp.sql
    ├── produtos_erp.sql
    ├── faturamento_erp.sql
    └── ... (other SQL files)
```

## Dependencies

- **cx_Oracle**: Oracle database connectivity (Oracle Instant Client auto-installed)
- **psycopg2-binary**: PostgreSQL connectivity
- **pandas**: Data manipulation and analysis
- **SQLAlchemy**: Database toolkit and ORM
- **python-dateutil**: Date/time utilities

### Oracle Instant Client

The setup script now automatically installs Oracle Instant Client 19.x, which is essential for connecting to Oracle databases. The installation:
- Downloads Oracle Client directly from Oracle's public repository
- Cleans any previous installations to avoid conflicts
- Configures environment variables automatically (avoiding duplicates)
- Sets up proper library paths and permissions
- Validates installation with comprehensive checks
- Falls back to manual installation if automatic download fails

**Important Notes:**
- The script handles reinstallation scenarios safely
- Environment variables are cleaned before being reset
- All Oracle Client files are verified after installation

## Security Considerations

### Credential Management
- **No hardcoded credentials**: All sensitive data uses environment variables
- **`.env` file**: Local configuration with restricted permissions (600)
- **`.gitignore` protection**: Prevents accidental commit of sensitive files
- **Environment-specific configs**: Different credentials for dev/prod

### Security Features
- **Validation**: Required credentials checked on startup
- **Fallback protection**: Safe defaults for development environment
- **SQL injection protection**: Parameterized queries throughout
- **Connection pooling**: Automatic cleanup and connection limits

### Setup Security
- Production setup creates `.env` automatically with proper permissions
- Local setup script for development environment
- Template file (`.env.example`) for safe reference
- Comprehensive security documentation in `SECURITY.md`

### Best Practices Enforced
```bash
# Production credentials in environment variables
ORACLE_PASSWORD=secure_production_password
POSTGRES_PASSWORD=secure_production_password

# File permissions automatically set to 600
chmod 600 .env

# Never commit sensitive files (enforced by .gitignore)
```