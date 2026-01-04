# Stock ETL Pipeline - Local Setup Guide

## Overview
This guide walks you through setting up and running the complete stock data ETL pipeline locally using Docker.

## Prerequisites

Before you start, ensure you have the following installed:

1. **Docker** (version 20.10+)
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version`

2. **Docker Compose** (version 2.0+)
   - Usually comes with Docker Desktop
   - Verify: `docker-compose --version`

3. **Git**
   - Verify: `git --version`

4. **System Requirements**
   - RAM: At least 8GB available
   - Disk Space: At least 20GB free
   - CPU: Multi-core recommended
   - OS: Linux, macOS, or Windows (with WSL2)

## Architecture Overview

The setup creates the following services:

```
Services Running Locally:
├── Zookeeper (2181)         - Kafka coordination
├── Kafka (9092)              - Message streaming
├── Kafka UI (8080)           - Kafka monitoring
├── PostgreSQL (5432)         - Metadata & data warehouse
├── LocalStack (4566)         - S3 emulation
├── Airflow Webserver (8888)  - DAG orchestration UI
├── Airflow Scheduler         - DAG scheduling
├── Prometheus (9090)         - Metrics collection
├── Grafana (3000)            - Metrics visualization
└── Stock Producer            - Data ingestion service
```

## Step-by-Step Setup

### Step 1: Clone Repository & Navigate

```bash
# Clone the repository
git clone <your-repository-url>
cd stock-etl-pipeline

# Create a working directory for data
mkdir -p data/kafka data/postgres data/localstack data/prometheus data/grafana
```

### Step 2: Configure Environment Variables

```bash
# Copy environment template to .env
cp .env.example .env

# Edit .env with your settings (optional, defaults work for local dev)
nano .env
```

**Key configuration options to consider:**

```bash
# Stock symbols to ingest
STOCKS=AAPL,GOOGL,MSFT,AMZN,TSLA

# Fetch interval in seconds (lower = more real-time)
FETCH_INTERVAL=300  # 5 minutes for demo, use 60 for faster testing

# Data warehouse type (postgres for free, or snowflake for trial)
DATA_WAREHOUSE_TYPE=postgres
USE_POSTGRES_AS_WAREHOUSE=true

# If using Snowflake, fill these in:
# SNOWFLAKE_ACCOUNT=your_account
# SNOWFLAKE_USER=your_user
# SNOWFLAKE_PASSWORD=your_password
```

### Step 3: Create Required Directory Structure

```bash
# Create all necessary directories
mkdir -p airflow/dags
mkdir -p airflow/plugins/operators
mkdir -p airflow/plugins/hooks
mkdir -p airflow/logs
mkdir -p airflow/config

mkdir -p data-ingestion/src
mkdir -p data-ingestion/logs

mkdir -p dbt/models/staging
mkdir -p dbt/models/intermediate
mkdir -p dbt/models/marts
mkdir -p dbt/tests
mkdir -p dbt/macros
mkdir -p dbt/seeds

mkdir -p great-expectations/checkpoints
mkdir -p great-expectations/expectations

mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/datasources

mkdir -p infrastructure/localstack
mkdir -p infrastructure/postgres
```

### Step 4: Copy Configuration Files

```bash
# Copy Prometheus configuration
cp prometheus.yml monitoring/prometheus/

# Copy PostgreSQL initialization script
cp init_postgres.sql infrastructure/postgres/

# Copy LocalStack initialization script
cp init_localstack.sh infrastructure/localstack/

# Copy Dockerfiles
cp airflow_dockerfile airflow/Dockerfile
cp producer_dockerfile data-ingestion/Dockerfile
cp airflow_requirements.txt airflow/requirements.txt
cp producer_requirements.txt data-ingestion/requirements.txt
```

### Step 5: Start Docker Services

```bash
# Build custom Docker images
docker-compose build

# Start all services in background
docker-compose up -d

# Monitor startup progress
docker-compose logs -f

# Wait for all services to be healthy (2-3 minutes)
```

**Watch for these signs of success:**

```
✓ zookeeper: healthy
✓ kafka: healthy
✓ postgres: healthy
✓ airflow-webserver: healthy
✓ airflow-scheduler: healthy
✓ localstack: healthy
✓ prometheus: healthy
✓ grafana: healthy
✓ stock-producer: starting
```

### Step 6: Verify Services Are Running

```bash
# Check all containers are running
docker-compose ps

# Expected output:
# CONTAINER ID   IMAGE                      STATUS
# xxx            zookeeper:latest           Up (healthy)
# xxx            kafka:latest               Up (healthy)
# xxx            postgres:15-alpine         Up (healthy)
# xxx            localstack:latest          Up (healthy)
# xxx            airflow-webserver:latest   Up (healthy)
# xxx            airflow-scheduler:latest   Up (healthy)
# xxx            prometheus:latest          Up (healthy)
# xxx            grafana:latest             Up (healthy)
# xxx            stock-producer:latest      Up
```

### Step 7: Access Web Interfaces

Open these in your browser:

1. **Airflow UI** (DAG Orchestration)
   - URL: http://localhost:8888
   - Username: `admin`
   - Password: `admin`
   - Action: Check DAGs, view execution history

2. **Kafka UI** (Stream Monitoring)
   - URL: http://localhost:8080
   - Action: Monitor topics, view messages

3. **PostgreSQL** (Database)
   - Host: localhost:5432
   - Username: `airflow`
   - Password: `airflow`
   - Database: `airflow`, `dbt_dev`
   - Tool: Use DBeaver, pgAdmin, or SQL CLI

4. **Prometheus** (Metrics)
   - URL: http://localhost:9090
   - Action: Query metrics, check targets

5. **Grafana** (Dashboards)
   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin`
   - Action: Add Prometheus datasource, create dashboards

6. **LocalStack S3**
   - Endpoint: http://localhost:4566
   - Access Key: `test`
   - Secret Key: `test`
   - Buckets: raw-stock-data, processed-stock-data

## Verifying Data Flow

### 1. Check Kafka Topics

```bash
# Connect to Kafka container
docker exec -it kafka bash

# List topics
kafka-topics --list --bootstrap-server kafka:9092

# Expected topics:
# stock_prices
# stock_volumes
# stock_metadata

# Consume messages (Ctrl+C to exit)
kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic stock_prices \
  --from-beginning
```

### 2. Check PostgreSQL Data

```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U airflow -d dbt_dev

# List tables
\dt raw_stocks.*

# Query stock prices
SELECT * FROM raw_stocks.stock_prices LIMIT 10;

# Check pipeline runs
SELECT * FROM raw_stocks.pipeline_runs ORDER BY created_at DESC LIMIT 5;

# Exit
\q
```

### 3. Check S3 / LocalStack

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# List S3 buckets (using aws-cli)
aws s3 ls --endpoint-url http://localhost:4566

# List objects in bucket
aws s3 ls s3://raw-stock-data/stock-data/raw/ \
  --endpoint-url http://localhost:4566 --recursive
```

### 4. View Airflow Logs

```bash
# View webserver logs
docker logs -f airflow-webserver

# View scheduler logs
docker logs -f airflow-scheduler

# View specific DAG logs
docker exec -it airflow-webserver \
  tail -f /home/airflow/logs/stock_etl_pipeline/*
```

### 5. Check Producer Health

```bash
# View producer logs
docker logs -f stock-producer

# Check producer metrics
curl http://localhost:8000/health

# Expected response: {"status": "healthy"}
```

## Common Setup Issues & Solutions

### Issue 1: Ports Already in Use

**Error**: `docker: Error response from daemon: Ports are not available`

**Solution**:
```bash
# Kill process on specific port (macOS/Linux)
lsof -ti:8888 | xargs kill -9

# Or change port in docker-compose.yml:
# airflow-webserver port mapping: "9999:8080" (change first number)
```

### Issue 2: Insufficient Memory

**Error**: `OOMKilled` or `Cannot create container`

**Solution**:
```bash
# Increase Docker memory limit
# Docker Desktop: Preferences → Resources → Memory (set to 8GB+)

# Or reduce services:
docker-compose down
docker-compose up -d kafka postgres airflow-webserver airflow-scheduler
```

### Issue 3: PostgreSQL Connection Failed

**Error**: `FATAL: Ident authentication failed`

**Solution**:
```bash
# Wait for PostgreSQL to fully initialize (can take 2-3 min)
docker logs postgres

# Recreate PostgreSQL:
docker-compose down postgres
docker volume rm stock-etl-pipeline_postgres_data
docker-compose up -d postgres
```

### Issue 4: Airflow DAGs Not Showing

**Error**: DAG list is empty in Airflow UI

**Solution**:
```bash
# Ensure DAGs are in correct directory
ls airflow/dags/

# Restart Airflow scheduler
docker-compose restart airflow-scheduler

# Check DAG syntax
docker exec -it airflow-webserver \
  python -m py_compile /home/airflow/dags/*.py
```

### Issue 5: Kafka Topics Not Created

**Error**: `Topic does not exist`

**Solution**:
```bash
# Manually create topics
docker exec -it kafka bash

kafka-topics --create \
  --bootstrap-server kafka:9092 \
  --topic stock_prices \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

exit
```

## Monitoring the Pipeline

### Real-Time Monitoring Checklist

- [ ] **Airflow**: Check DAG runs every minute
- [ ] **Kafka UI**: Verify messages flowing into topics
- [ ] **Prometheus**: Monitor CPU, memory, request rates
- [ ] **Grafana**: Set up custom dashboards
- [ ] **PostgreSQL**: Query data freshness
- [ ] **Logs**: Tail Docker logs for errors

### Key Metrics to Monitor

```bash
# Kafka consumer lag
docker exec kafka kafka-consumer-groups \
  --bootstrap-server kafka:9092 \
  --group airflow-stock-consumer \
  --describe

# Airflow task duration
SELECT dag_id, task_id, AVG(duration) 
FROM task_instance 
GROUP BY dag_id, task_id;

# Data freshness
SELECT MAX(timestamp) FROM raw_stocks.stock_prices;
```

## Shutting Down Services

```bash
# Gracefully stop all services
docker-compose down

# Stop and remove volumes (⚠️ WARNING: Deletes data)
docker-compose down -v

# View stopped containers
docker-compose ps -a

# Restart specific service
docker-compose up -d airflow-webserver
```

## Troubleshooting Commands

```bash
# View all container logs
docker-compose logs

# View specific service logs (last 100 lines)
docker logs --tail=100 airflow-webserver

# Execute command in container
docker exec -it postgres psql -U airflow

# Restart a service
docker-compose restart airflow-scheduler

# Rebuild a service
docker-compose up -d --build airflow-webserver

# Remove unused images/volumes
docker system prune

# Inspect network
docker network inspect stock-etl-pipeline_stock-pipeline
```

## Next Steps

Once services are running successfully:

1. **Deploy Airflow DAGs** (see DAGs section)
2. **Deploy DBT Models** (see DBT section)
3. **Configure Great Expectations** (see Data Quality section)
4. **Create Tableau Dashboards** (see Visualization section)
5. **Set Up Monitoring** (see Monitoring section)

## Performance Tuning

For better performance:

```bash
# Increase Airflow parallelism
export AIRFLOW__CORE__PARALLELISM=8
export AIRFLOW__CORE__DAG_CONCURRENCY=4

# Increase Kafka partitions
kafka-topics --alter --topic stock_prices \
  --partitions 6 --bootstrap-server kafka:9092

# Increase PostgreSQL connections
# Edit postgresql.conf: max_connections=200
```

## System Cleanup

```bash
# Stop everything
docker-compose down -v

# Remove all Docker images
docker rmi $(docker images -q)

# Remove all dangling volumes
docker volume prune -f

# Full reset (remove all Docker data)
docker system prune -a --volumes
```

---

**Need help?** Check logs with:
```bash
docker-compose logs | grep -i error
```

**Want to reset everything?**
```bash
bash scripts/reset-environment.sh
```

