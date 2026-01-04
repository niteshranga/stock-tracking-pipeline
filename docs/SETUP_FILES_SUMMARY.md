# Stock ETL Pipeline - Setup Files Summary

This document summarizes all the infrastructure and configuration files created for the stock ETL pipeline project.

## Files Created

### 1. Docker Compose Orchestration
**File**: `docker-compose.yml`
- **Purpose**: Orchestrates all services (Kafka, PostgreSQL, Airflow, LocalStack, Prometheus, Grafana, etc.)
- **Key Services**:
  - Zookeeper & Kafka (streaming)
  - PostgreSQL (metadata & data warehouse)
  - Airflow (orchestration)
  - LocalStack (S3 emulation)
  - Prometheus & Grafana (monitoring)
  - Stock Producer (data ingestion)
- **Ports**: 
  - Airflow: 8888
  - Kafka UI: 8080
  - Prometheus: 9090
  - Grafana: 3000
  - LocalStack: 4566
  - PostgreSQL: 5432

### 2. Environment Configuration
**File**: `.env.example`
- **Purpose**: Template for environment variables
- **Contents**:
  - Kafka configuration (bootstrap servers, topics, retention)
  - Airflow settings (executor, database, connections)
  - PostgreSQL credentials
  - AWS/LocalStack configuration
  - Snowflake credentials (optional)
  - DBT settings
  - Monitoring parameters
  - Data quality thresholds
- **Usage**: Copy to `.env` and customize for your environment

### 3. Airflow Docker Image
**File**: `airflow_dockerfile`
- **Purpose**: Custom Apache Airflow image with all dependencies
- **Includes**:
  - Python 3.11
  - Airflow 2.7.3
  - System dependencies (PostgreSQL client, curl, git)
  - All Python packages from requirements.txt
- **Volumes**: DAGs, plugins, logs, config directories

### 4. Airflow Dependencies
**File**: `airflow_requirements.txt`
- **Purpose**: Python packages for Airflow
- **Key Packages**:
  - Apache Airflow providers (Kafka, PostgreSQL, Amazon S3)
  - Data processing (pandas, numpy, pyarrow)
  - Cloud & storage (boto3, snowflake-connector)
  - Data validation (Great Expectations, jsonschema)
  - DBT integration
  - Monitoring (prometheus-client, sentry-sdk)
  - Stock data APIs (yfinance, alpha-vantage)

### 5. Producer Docker Image
**File**: `producer_dockerfile`
- **Purpose**: Docker image for stock data producer service
- **Includes**:
  - Python 3.11
  - System dependencies
  - Python packages for data fetching and Kafka publishing
- **Volumes**: Source code, logs

### 6. Producer Dependencies
**File**: `producer_requirements.txt`
- **Purpose**: Python packages for data ingestion service
- **Key Packages**:
  - yfinance, alpha-vantage (data fetching)
  - kafka-python, confluent-kafka (streaming)
  - Data validation (jsonschema, marshmallow)
  - Error handling (tenacity for retries)

### 7. LocalStack Initialization
**File**: `init_localstack.sh`
- **Purpose**: Automatically set up S3 buckets when LocalStack starts
- **Creates**:
  - `raw-stock-data` bucket (data lake)
  - `processed-stock-data` bucket (transformed data)
  - `archive-stock-data` bucket (archived data)
  - Folder structure: `year=YYYY/month=MM/day=DD/`
- **Usage**: Automatically runs via docker-compose volume mount

### 8. PostgreSQL Initialization
**File**: `init_postgres.sql`
- **Purpose**: Set up PostgreSQL databases, users, and tables at startup
- **Creates**:
  - `dbt_dev` database for DBT transformations
  - `dbt_user` with appropriate permissions
  - Schemas: raw_stocks, stg_stocks, int_stocks, marts_stocks
  - Tables:
    - `stock_prices`: Raw stock data
    - `pipeline_runs`: Pipeline execution tracking
    - `data_quality_metrics`: Data quality check results
  - Indexes for performance
- **Usage**: Automatically runs via docker-compose volume mount

### 9. Prometheus Configuration
**File**: `prometheus.yml`
- **Purpose**: Configure metrics scraping for monitoring
- **Scrape Targets**:
  - Prometheus itself
  - Airflow Webserver & Scheduler
  - PostgreSQL
  - Kafka
  - LocalStack
  - Grafana
  - Stock Producer
- **Scrape Interval**: 15-30 seconds
- **Data Retention**: Configurable

### 10. Git Ignore
**File**: `.gitignore`
- **Purpose**: Prevent committing sensitive files and build artifacts
- **Excludes**:
  - Environment files (`.env`)
  - Python artifacts (`__pycache__`, `*.pyc`)
  - IDE files (`.vscode`, `.idea`)
  - Logs and temporary files
  - Credentials and keys
  - Large data files
  - Docker volumes

### 11. Setup Guide
**File**: `SETUP_GUIDE.md`
- **Purpose**: Comprehensive guide for local development setup
- **Contents**:
  - Prerequisites and installation
  - Architecture overview
  - Step-by-step setup instructions
  - Web interface access instructions
  - Data flow verification steps
  - Troubleshooting guide
  - Common issues and solutions
  - Monitoring checklist
  - Shutdown and cleanup procedures

## File Organization

```
project-root/
├── docker-compose.yml          # Main orchestration
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── SETUP_GUIDE.md              # Setup instructions
│
├── airflow/
│   ├── Dockerfile              # Custom Airflow image
│   └── requirements.txt         # Airflow dependencies
│
├── data-ingestion/
│   ├── Dockerfile              # Producer image
│   └── requirements.txt         # Producer dependencies
│
├── infrastructure/
│   ├── localstack/
│   │   └── init-aws.sh          # S3 bucket setup
│   ├── postgres/
│   │   └── init-dbt.sql         # PostgreSQL setup
│   └── terraform/               # IaC templates (future)
│
└── monitoring/
    └── prometheus/
        └── prometheus.yml       # Metrics configuration
```

## Service Startup Sequence

```
1. Zookeeper (2181)
   ↓
2. Kafka (9092, 29092)
   ↓
3. PostgreSQL (5432)
   ├─ Creates dbt_dev database
   ├─ Creates raw_stocks schema & tables
   └─ Initializes airflow metadata
   ↓
4. LocalStack (4566)
   ├─ Creates raw-stock-data bucket
   ├─ Creates processed-stock-data bucket
   └─ Sets up S3 folder structure
   ↓
5. Prometheus (9090)
   ↓
6. Grafana (3000)
   ↓
7. Airflow Webserver (8888)
   ├─ Initializes Airflow database
   └─ Creates admin user
   ↓
8. Airflow Scheduler
   └─ Starts scheduling DAGs
   ↓
9. Kafka UI (8080)
   ↓
10. Stock Producer
    └─ Starts fetching & publishing data
```

## Key Configuration Decisions

### 1. PostgreSQL vs Snowflake
- **Current Setup**: PostgreSQL (free, local)
- **Alternative**: Snowflake (free trial with $400 credits)
- **Decision Point**: Change `USE_POSTGRES_AS_WAREHOUSE` in `.env`

### 2. Data Source Options
- **Default**: yfinance (free, no API key)
- **Alternative**: Alpha Vantage (free tier with rate limiting)
- **Configuration**: Set `DATA_SOURCE` in `.env`

### 3. Fetch Interval
- **Development**: 300 seconds (5 minutes) - faster iterations
- **Demo**: 60 seconds (1 minute) - show real-time flow
- **Production**: 60-300 seconds depending on use case
- **Configuration**: Set `FETCH_INTERVAL` in `.env`

### 4. Kafka Partitions
- **Current**: 3 partitions (good balance for local dev)
- **Production**: Match number of consumers/brokers
- **Configuration**: `KAFKA_PARTITIONS` in docker-compose.yml

## Resource Requirements

### Minimum
- RAM: 8GB available
- CPU: Dual-core
- Disk: 20GB free

### Recommended
- RAM: 16GB available
- CPU: Quad-core
- Disk: 50GB free

### All Services Running
- RAM usage: ~4-6GB
- Disk usage: ~5-10GB (grows with data)
- Network: No external internet required (except for stock data API)

## Next Steps After Setup

1. **Copy these files to your GitHub repository**
   ```bash
   git add docker-compose.yml .env.example .gitignore airflow/ infrastructure/ monitoring/
   git commit -m "Add Docker infrastructure and setup files"
   git push
   ```

2. **Follow SETUP_GUIDE.md** to start services locally

3. **Create application code files**:
   - Kafka producer (`data-ingestion/src/producer.py`)
   - Airflow DAGs (`airflow/dags/stock_etl_pipeline.py`)
   - DBT models (`dbt/models/`)
   - Great Expectations configs (`great-expectations/`)

4. **Add CI/CD**:
   - GitHub Actions workflows
   - Automated testing
   - Code quality checks

## Files Not Yet Created

The following will be created in subsequent steps:

### Application Code
- [ ] `data-ingestion/src/producer.py` - Kafka producer
- [ ] `data-ingestion/src/data_fetcher.py` - Stock data API wrapper
- [ ] `data-ingestion/tests/` - Unit tests

### Airflow
- [ ] `airflow/dags/stock_etl_pipeline.py` - Main ETL DAG
- [ ] `airflow/dags/data_quality_checks.py` - Quality check DAG
- [ ] `airflow/plugins/operators/` - Custom operators
- [ ] `airflow/plugins/hooks/` - Custom hooks

### DBT
- [ ] `dbt/dbt_project.yml` - DBT configuration
- [ ] `dbt/profiles.yml` - Database connections
- [ ] `dbt/models/staging/` - Raw data staging
- [ ] `dbt/models/intermediate/` - Aggregations
- [ ] `dbt/models/marts/` - Final business tables
- [ ] `dbt/tests/` - Data tests

### Great Expectations
- [ ] `great-expectations/great_expectations.yml` - Configuration
- [ ] `great-expectations/checkpoints/` - Validation checkpoints
- [ ] `great-expectations/expectations/` - Expectation suites

### Documentation & Scripts
- [ ] `README.md` - Project overview
- [ ] `ARCHITECTURE.md` - Architecture documentation
- [ ] `scripts/setup-local-env.sh` - One-command setup
- [ ] `scripts/start-services.sh` - Start services script
- [ ] `scripts/stop-services.sh` - Stop services script
- [ ] `scripts/health-check.sh` - Health verification

## Testing the Setup

After running Docker Compose:

```bash
# 1. Verify containers are running
docker-compose ps

# 2. Check Kafka is receiving data
docker exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic stock_prices --from-beginning

# 3. Query PostgreSQL
docker exec postgres psql -U airflow -d dbt_dev -c "SELECT * FROM raw_stocks.stock_prices LIMIT 1;"

# 4. Access Airflow UI
# Open browser to http://localhost:8888

# 5. Access Kafka UI
# Open browser to http://localhost:8080
```

## Troubleshooting Checklist

- [ ] Docker is running and has enough memory (8GB+)
- [ ] All required ports are available (8888, 8080, 4566, 5432, etc.)
- [ ] `.env` file exists and is readable
- [ ] Network connectivity (ping to services)
- [ ] Logs checked for errors: `docker-compose logs`
- [ ] Services are healthy: `docker-compose ps` shows "Up (healthy)"

---

**Questions?** Refer to `SETUP_GUIDE.md` for detailed troubleshooting steps.
