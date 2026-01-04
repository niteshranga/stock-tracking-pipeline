# Stock ETL Pipeline - Docker Setup Files Index

## Overview

This package contains all the Docker infrastructure and configuration files needed to run the complete stock ETL pipeline locally. All services are containerized and orchestrated using Docker Compose.

**Total Files**: 14 core setup files  
**Setup Time**: ~5-10 minutes (after Docker installation)  
**System Requirements**: 8GB RAM, 20GB disk space

---

## File Descriptions & Usage

### 1. **docker-compose.yml** ⭐ (MAIN FILE)
**Size**: 8.4 KB

The main orchestration file that defines all services and how they interact.

**What it does:**
- Defines 10 services (Kafka, PostgreSQL, Airflow, LocalStack, Prometheus, Grafana, etc.)
- Sets up networking between containers
- Configures volumes for data persistence
- Defines health checks for service readiness
- Maps ports for web access

**Services included:**
```
├── Zookeeper & Kafka (streaming)
├── PostgreSQL (databases)
├── LocalStack (S3 emulation)
├── Airflow Webserver & Scheduler (orchestration)
├── Prometheus & Grafana (monitoring)
├── Kafka UI (web interface)
└── Stock Producer (data ingestion)
```

**To use:**
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# Stop all services
docker-compose down
```

---

### 2. **.env.example** (CONFIGURATION TEMPLATE)
**Size**: 5.5 KB

Environment variables template for customizing the setup.

**What it contains:**
- Kafka configuration (topics, partitions, retention)
- Airflow settings (executor, database connections)
- PostgreSQL credentials
- AWS/LocalStack settings
- Snowflake credentials (optional)
- DBT configuration
- Monitoring thresholds
- Development flags

**Key variables to customize:**
```bash
# Stock symbols to fetch
STOCKS=AAPL,GOOGL,MSFT,AMZN,TSLA

# How often to fetch data (seconds)
FETCH_INTERVAL=300

# Data warehouse type (postgres or snowflake)
USE_POSTGRES_AS_WAREHOUSE=true
DATA_WAREHOUSE_TYPE=postgres
```

**To use:**
```bash
# Copy template to actual .env file
cp .env.example .env

# Edit with your preferences
nano .env

# Docker Compose automatically loads .env
```

---

### 3. **airflow_dockerfile** (AIRFLOW IMAGE)
**Size**: 782 bytes

Custom Docker image for Apache Airflow with all required dependencies.

**What it does:**
- Starts from `apache/airflow:2.7.3-python3.11`
- Installs system dependencies (PostgreSQL client, curl, git)
- Installs Python packages from requirements.txt
- Creates necessary directories
- Configures the Airflow working directory

**Build & run:**
```bash
# Docker Compose builds automatically
docker-compose up -d airflow-webserver

# Or manually:
docker build -f airflow_dockerfile -t stock-airflow:latest .
```

---

### 4. **airflow_requirements.txt** (AIRFLOW DEPENDENCIES)
**Size**: 1.3 KB

Python packages needed for Apache Airflow and all integrations.

**Key packages:**
- **Airflow**: 2.7.3
- **Providers**: Kafka, PostgreSQL, Amazon S3
- **Data Processing**: pandas, numpy, pyarrow
- **Cloud**: boto3, snowflake-connector, s3fs
- **Data Quality**: Great Expectations
- **DBT**: dbt-core, dbt-postgres, dbt-snowflake
- **Monitoring**: prometheus-client, sentry-sdk
- **APIs**: yfinance, alpha-vantage

**Usage:**
- Automatically used by airflow_dockerfile
- Can be updated to add new dependencies
- Format: standard pip requirements file

---

### 5. **producer_dockerfile** (DATA PRODUCER IMAGE)
**Size**: 769 bytes

Docker image for the stock data producer service.

**What it does:**
- Creates a lightweight Python container
- Installs dependencies from producer_requirements.txt
- Runs the Kafka producer application
- Includes health check

**Responsibilities:**
- Fetches stock data from free APIs (yfinance, Alpha Vantage)
- Publishes messages to Kafka topics
- Handles errors and retries
- Logs to stdout for Docker

---

### 6. **producer_requirements.txt** (PRODUCER DEPENDENCIES)
**Size**: 551 bytes

Python packages for the data ingestion service.

**Key packages:**
- **Data Fetching**: yfinance, alpha-vantage, pandas
- **Streaming**: kafka-python, confluent-kafka
- **Validation**: jsonschema, marshmallow
- **Error Handling**: tenacity (retry logic)
- **Configuration**: python-dotenv, pydantic

---

### 7. **init_localstack.sh** (S3 SETUP SCRIPT)
**Size**: 1.9 KB

Bash script that automatically sets up LocalStack S3 when the container starts.

**What it does:**
- Waits for LocalStack to be ready
- Creates S3 buckets:
  - `raw-stock-data` (data lake)
  - `processed-stock-data` (transformed data)
  - `archive-stock-data` (archived data)
- Creates folder structure by date:
  - `stock-data/raw/year=YYYY/month=MM/day=DD/`
  - `stock-data/processed/year=YYYY/month=MM/day=DD/`
  - `stock-data/archive/year=YYYY/month=MM/`

**Run automatically via:**
```yaml
volumes:
  - "./infrastructure/localstack/init-aws.sh:/docker-entrypoint-initaws.d/init-aws.sh"
```

**Manual execution:**
```bash
docker exec localstack bash /docker-entrypoint-initaws.d/init-aws.sh
```

---

### 8. **init_postgres.sql** (DATABASE SETUP)
**Size**: 5.1 KB

SQL script that sets up PostgreSQL databases, users, and tables at startup.

**What it creates:**

**Databases:**
- `airflow` - Airflow metadata (created by docker-compose)
- `dbt_dev` - DBT models and transformations

**Users:**
- `airflow` - Airflow default user
- `dbt_user` - DBT operations user (password: dbt_password)

**Schemas** (in dbt_dev):
- `raw_stocks` - Raw data from ingestion
- `stg_stocks` - Staged/cleaned data
- `int_stocks` - Intermediate transformations
- `marts_stocks` - Final business tables

**Tables** (in raw_stocks schema):
- `stock_prices` - Raw stock OHLCV data
- `pipeline_runs` - Execution tracking
- `data_quality_metrics` - Quality check results

**Indexes** for performance on:
- symbol + timestamp (stock prices)
- fetched_at (data freshness)
- run_date, status (pipeline tracking)

**Run automatically via:**
```yaml
volumes:
  - "./infrastructure/postgres/init-dbt.sql:/docker-entrypoint-initdb.d/init-dbt.sql"
```

**Manual execution:**
```bash
docker exec postgres psql -U airflow < init_postgres.sql
```

---

### 9. **prometheus.yml** (MONITORING CONFIG)
**Size**: 1.6 KB

Prometheus configuration for metrics collection and monitoring.

**What it does:**
- Defines scrape jobs for all services
- Sets scrape interval to 15-30 seconds
- Configures data retention
- Targets monitored:
  - Prometheus itself (metrics about metrics!)
  - Airflow (webserver & scheduler)
  - PostgreSQL
  - Kafka
  - LocalStack
  - Grafana
  - Stock Producer

**Usage:**
```bash
# Access Prometheus UI
# http://localhost:9090

# Query metrics
# Example: airflow_dag_run_duration_seconds
```

**Customization:**
- Adjust `scrape_interval` for more/less frequent metrics
- Add new scrape configs for additional services
- Modify `external_labels` for custom identifiers

---

### 10. **.gitignore** (GIT CONFIGURATION)
**Size**: 1.4 KB

Prevents committing sensitive and unnecessary files to Git.

**What it excludes:**
- Environment files (`.env`, credentials)
- Python artifacts (`__pycache__`, `.pyc`)
- IDE files (`.vscode`, `.idea`)
- Logs and temporary files
- Docker volumes and data
- Large data files (CSV, Parquet, JSON)
- OS files (`.DS_Store`, `Thumbs.db`)

**Usage:**
```bash
# Use as-is for the project
cp .gitignore <your-repo-root>/

# No action needed - Git automatically respects it
```

---

### 11. **SETUP_GUIDE.md** (DETAILED INSTRUCTIONS)
**Size**: 12 KB

Comprehensive step-by-step guide for setting up and running the pipeline locally.

**Sections:**
1. **Prerequisites** - What you need before starting
2. **Architecture Overview** - Service diagram
3. **Step-by-Step Setup** - 7 detailed steps
4. **Web Access** - How to access each service
5. **Data Flow Verification** - Verify everything works
6. **Troubleshooting** - Solutions to common issues
7. **Monitoring** - How to monitor the pipeline
8. **Shutdown & Cleanup** - Clean shutdown procedures
9. **Performance Tuning** - Optimize for your system

**To use:**
```bash
# Follow from step 1 to completion
# Takes about 10-15 minutes for initial setup
# Subsequent starts are much faster
```

**Key commands from guide:**
```bash
cp .env.example .env
docker-compose build
docker-compose up -d
docker-compose ps
```

---

### 12. **SETUP_FILES_SUMMARY.md** (OVERVIEW)
**Size**: 11 KB

Summary of all setup files and their purposes.

**Contains:**
- File-by-file explanations
- Service startup sequence
- Key configuration decisions
- Resource requirements
- Startup verification steps
- Troubleshooting checklist

**Useful for understanding:**
- Why each file exists
- How files interact
- What to customize
- What's created automatically

---

### 13. **stock_etl_pipeline_blueprint.md** (PROJECT BLUEPRINT)
**Size**: 20 KB

Complete project blueprint showing the full architecture and scope.

**Includes:**
- Project overview
- Complete repository structure
- Data flow diagrams
- Technology decisions & rationale
- Feature descriptions
- Milestone breakdown
- Expected portfolio outcomes

**References this guide** to understand the big picture before diving into setup.

---

### 14. **INDEX.md** (THIS FILE)
**Size**: This file

Navigation guide explaining all setup files and how to use them.

---

## Quick Start Guide

### Step 1: Prepare
```bash
# Copy environment template
cp .env.example .env

# (Optional) Edit .env if you want to change stock symbols, etc.
nano .env
```

### Step 2: Start Services
```bash
# Build images and start all services
docker-compose up -d

# Wait for services to be healthy (2-3 minutes)
docker-compose ps
```

### Step 3: Verify Services
```bash
# Check all containers are running
docker-compose ps

# Expected status: "Up (healthy)" for most services

# View logs to check for errors
docker-compose logs | head -100
```

### Step 4: Access Web Interfaces
- **Airflow**: http://localhost:8888 (admin/admin)
- **Kafka UI**: http://localhost:8080
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **PostgreSQL**: localhost:5432 (airflow/airflow)

### Step 5: Verify Data Flow
```bash
# Check Kafka topics
docker exec kafka kafka-topics --list --bootstrap-server kafka:9092

# Query PostgreSQL
docker exec postgres psql -U airflow -d dbt_dev \
  -c "SELECT * FROM raw_stocks.stock_prices LIMIT 5;"

# Check S3 buckets
docker exec localstack awslocal s3 ls --recursive
```

---

## File Placement in Your Project

After reviewing these files, place them in your GitHub repository as follows:

```
your-repo/
├── docker-compose.yml          ← Main orchestration file
├── .env.example                ← Environment template
├── .gitignore                  ← Git configuration
│
├── airflow/
│   ├── Dockerfile              ← Rename from airflow_dockerfile
│   └── requirements.txt         ← Rename from airflow_requirements.txt
│
├── data-ingestion/
│   ├── Dockerfile              ← Rename from producer_dockerfile
│   └── requirements.txt         ← Rename from producer_requirements.txt
│
├── infrastructure/
│   ├── localstack/
│   │   └── init-aws.sh          ← Rename from init_localstack.sh
│   ├── postgres/
│   │   └── init-dbt.sql         ← Rename from init_postgres.sql
│   └── terraform/               ← Future IaC
│
├── monitoring/
│   └── prometheus/
│       └── prometheus.yml       ← Prometheus config
│
└── docs/
    ├── SETUP_GUIDE.md           ← Setup instructions
    ├── SETUP_FILES_SUMMARY.md   ← File overview
    ├── ARCHITECTURE.md          ← Architecture explanation
    └── INDEX.md                 ← Navigation (this file)
```

---

## Common Workflows

### Start Fresh Development Session
```bash
docker-compose up -d
# Services automatically start
```

### Check Service Health
```bash
docker-compose ps
docker-compose logs --tail=50
```

### Debug a Specific Service
```bash
# View logs
docker logs -f airflow-webserver

# Execute command in container
docker exec -it airflow-webserver bash

# View a specific DAG
docker exec airflow-webserver cat /home/airflow/dags/stock_etl_pipeline.py
```

### Reset Everything
```bash
docker-compose down -v
docker-compose up -d
# All databases and volumes recreated
```

### Access PostgreSQL Directly
```bash
docker exec -it postgres psql -U airflow -d dbt_dev
# Interactive SQL shell
```

### Monitor in Real-Time
```bash
# View all logs with timestamps
docker-compose logs -f --timestamps

# View specific service
docker logs -f airflow-scheduler
```

---

## Important Notes

### Security ⚠️
- Default credentials (`admin/admin`) are **for local development only**
- `.env.example` contains test credentials - change before production
- `.gitignore` prevents committing `.env` files to Git
- Don't push sensitive data to GitHub

### Storage
- PostgreSQL data persists in `postgres_data/` volume
- LocalStack S3 data persists in `localstack_data/` volume
- Logs persist in `airflow/logs/` directory
- Delete volumes with `docker-compose down -v` (⚠️ deletes all data)

### Networking
- All services communicate via Docker network: `stock-pipeline`
- External access via localhost ports (8888, 8080, 9090, etc.)
- No internet required (except for stock data API calls)

### Performance
- First startup takes 2-3 minutes (image building + initialization)
- Subsequent startups take ~30-60 seconds
- Adjust `AIRFLOW__CORE__PARALLELISM` for more concurrency
- Increase Kafka partitions for higher throughput

---

## Troubleshooting Quick Links

**Port Already in Use?**
→ See SETUP_GUIDE.md → Common Setup Issues → Issue 1

**PostgreSQL Won't Start?**
→ See SETUP_GUIDE.md → Common Setup Issues → Issue 3

**Airflow DAGs Not Showing?**
→ See SETUP_GUIDE.md → Common Setup Issues → Issue 4

**Out of Memory?**
→ See SETUP_GUIDE.md → Common Setup Issues → Issue 2

---

## What's Next?

After verifying the setup works, you'll create:

1. **Data Ingestion Service** (`data-ingestion/src/producer.py`)
2. **Airflow DAGs** (`airflow/dags/stock_etl_pipeline.py`)
3. **DBT Models** (`dbt/models/`)
4. **Great Expectations Configs** (`great-expectations/`)
5. **Tableau Dashboards** (visualization layer)

All of these will use these docker setup files as the foundation.

---

## Reference Commands

```bash
# View container status
docker-compose ps

# View all logs
docker-compose logs

# View specific service logs
docker logs -f <service-name>

# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Remove everything (keeps images)
docker-compose down

# Remove everything (including volumes - ⚠️ deletes data)
docker-compose down -v

# Rebuild images
docker-compose build

# Execute command
docker exec <container-name> <command>

# View resource usage
docker stats
```

---

**Next Step**: Follow **SETUP_GUIDE.md** to get everything running! 🚀
