# Real-Time Stock Data ETL Pipeline - Project Blueprint

## Project Overview
A complete end-to-end ETL pipeline demonstrating real-time stock data ingestion, processing, transformation, and visualization using cloud-native tools and best practices.

**Tech Stack:**
- **Streaming**: Apache Kafka
- **Storage**: LocalStack (AWS S3 emulation) + Snowflake (free trial tier)
- **Orchestration**: Apache Airflow
- **Transformation**: DBT (Data Build Tool)
- **Data Quality**: Great Expectations
- **Visualization**: Tableau Public (free) / Open-source tools
- **Containerization**: Docker & Docker Compose
- **Language**: Python, SQL

**Key Features:**
- ✅ Real-time data streaming with Kafka
- ✅ Schema validation and data quality checks
- ✅ Error handling and retry logic
- ✅ Incremental data loading (ELT pattern)
- ✅ Data lineage and monitoring
- ✅ Docker-based local development environment
- ✅ Infrastructure as Code (Docker Compose)

---

## GitHub Repository Structure

```
stock-etl-pipeline/
│
├── README.md                          # Project overview, setup guide, architecture diagram
├── ARCHITECTURE.md                    # Detailed architecture documentation
├── CONTRIBUTING.md                    # Contribution guidelines
├── LICENSE                            # MIT License
├── .gitignore                         # Git ignore rules
│
├── docker-compose.yml                 # Orchestrate all services locally
├── .env.example                       # Environment variables template
│
├── docs/
│   ├── project-structure.md           # This file
│   ├── setup-guide.md                 # Step-by-step local setup
│   ├── architecture-diagram.md        # Visual architecture explanation
│   ├── data-flow.md                   # Data flow documentation
│   └── troubleshooting.md             # Common issues & solutions
│
├── kafka/
│   ├── Dockerfile                     # Kafka Docker image
│   ├── config/
│   │   └── server.properties          # Kafka broker configuration
│   └── scripts/
│       ├── create-topics.sh           # Create Kafka topics
│       └── produce-sample-data.py     # Sample data producer (for testing)
│
├── data-ingestion/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── producer.py                # Kafka producer - fetches stock data
│   │   ├── data_fetcher.py            # Free API integration (yfinance, Alpha Vantage free tier)
│   │   └── config.py                  # Configuration management
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                     # Docker image for producer
│   └── tests/
│       ├── __init__.py
│       ├── test_producer.py
│       └── test_data_fetcher.py
│
├── airflow/
│   ├── Dockerfile                     # Custom Airflow image
│   ├── dags/
│   │   ├── __init__.py
│   │   ├── stock_etl_pipeline.py      # Main DAG orchestrating the pipeline
│   │   ├── data_quality_checks.py     # Data quality DAG
│   │   └── config.py                  # DAG configuration
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── operators/
│   │   │   ├── __init__.py
│   │   │   ├── kafka_consumer_operator.py
│   │   │   ├── s3_operator.py
│   │   │   └── snowflake_operator.py
│   │   └── hooks/
│   │       ├── __init__.py
│   │       ├── kafka_hook.py
│   │       ├── s3_hook.py
│   │       └── snowflake_hook.py
│   ├── logs/                          # Airflow logs (gitignored)
│   ├── requirements.txt               # Airflow + dependencies
│   └── config/
│       └── airflow.cfg                # Airflow configuration
│
├── dbt/
│   ├── dbt_project.yml                # DBT project configuration
│   ├── profiles.yml                   # Snowflake connection profile
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_stock_prices.sql   # Raw data cleaning
│   │   │   ├── stg_stock_volumes.sql
│   │   │   └── sources.yml            # Source definitions
│   │   ├── intermediate/
│   │   │   ├── int_stock_daily_agg.sql # Daily aggregations
│   │   │   └── int_stock_metrics.sql   # Calculated metrics
│   │   └── marts/
│   │       ├── fact_stock_daily.sql   # Fact table
│   │       ├── dim_stocks.sql         # Dimension table
│   │       └── schema.yml             # Table documentation & tests
│   ├── tests/
│   │   ├── accepted_values_symbols.sql # Custom tests
│   │   └── unique_date_symbol.sql
│   ├── macros/
│   │   ├── generate_alias_name.sql    # Macro for table naming
│   │   └── custom_tests.sql           # Custom test macros
│   ├── seeds/                         # Reference data
│   │   └── stock_symbols.csv
│   └── requirements.txt               # DBT + adapters
│
├── great-expectations/
│   ├── great_expectations.yml         # GX configuration
│   ├── checkpoints/
│   │   ├── stock_data_checkpoint.yml  # Data quality checkpoint
│   │   └── daily_aggregation_checkpoint.yml
│   ├── expectations/
│   │   ├── stock_prices_expectation.json
│   │   └── volumes_expectation.json
│   ├── plugins/
│   │   └── custom_expectations.py     # Custom validation rules
│   └── notebooks/
│       └── generate_expectations.ipynb # Exploratory notebook
│
├── visualization/
│   ├── tableau/
│   │   ├── dashboards/
│   │   │   ├── real-time-stock-monitor.twb
│   │   │   ├── data-quality-dashboard.twb
│   │   │   └── pipeline-metrics.twb
│   │   └── README.md
│   └── scripts/
│       └── export_to_tableau_public.py # Script to publish to Tableau Public
│
├── infrastructure/
│   ├── localstack/
│   │   ├── Dockerfile                 # LocalStack custom image
│   │   ├── init-aws.sh                # Initialize S3 buckets & structure
│   │   └── config.sh
│   ├── snowflake/
│   │   ├── setup.sql                  # Snowflake initial setup
│   │   ├── warehouse-config.sql       # Warehouse & database setup
│   │   └── iam-roles.sql              # Role-based access control
│   └── terraform/                     # IaC templates (optional, for future cloud deployment)
│       ├── main.tf
│       └── variables.tf
│
├── scripts/
│   ├── setup-local-env.sh             # One-command setup script
│   ├── start-services.sh              # Start all Docker containers
│   ├── stop-services.sh               # Stop all services
│   ├── health-check.sh                # Service health verification
│   ├── reset-environment.sh           # Clean reset (careful!)
│   └── generate-test-data.py          # Generate synthetic stock data for testing
│
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml             # Metrics scraping config
│   │   └── Dockerfile
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   └── pipeline-monitoring.json
│   │   └── datasources.yml
│   └── README.md
│
├── tests/
│   ├── integration/
│   │   ├── test_kafka_to_s3.py        # Integration tests
│   │   ├── test_s3_to_snowflake.py
│   │   └── test_dbt_transformations.py
│   └── unit/
│       ├── test_data_quality.py
│       └── test_schema_validation.py
│
├── config/
│   ├── development.env
│   ├── production.env
│   └── schemas/
│       ├── stock_data_schema.json     # JSON Schema for validation
│       └── expected_columns.yml
│
└── requirements-all.txt               # Combined requirements file
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    REAL-TIME STOCK DATA PIPELINE                   │
└─────────────────────────────────────────────────────────────────────┘

1. DATA INGESTION LAYER
   ┌──────────────────────────────────┐
   │  Free Stock Data Source           │
   │  (yfinance / Alpha Vantage)       │
   └──────────────┬───────────────────┘
                  │
   ┌──────────────▼───────────────────┐
   │  Python Kafka Producer            │
   │  - Fetch stock prices (real-time) │
   │  - Serialize to JSON              │
   │  - Error handling & retry logic   │
   └──────────────┬───────────────────┘

2. STREAMING LAYER
   ┌──────────────▼───────────────────┐
   │  Apache Kafka (Docker)            │
   │  - Topics: stock_prices, volumes  │
   │  - Partitions: by symbol          │
   │  - Retention: configurable        │
   └──────────────┬───────────────────┘

3. STORAGE LAYER (Dual Storage)
   ┌──────────────▼───────────────────┐
   │  LocalStack S3 (Data Lake)        │
   │  - Raw data storage               │
   │  - Partitioned: s3://stock-data/  │
   │    year=YYYY/month=MM/day=DD/     │
   └──────────┬──────────────┬─────────┘
              │              │
   ┌──────────▼─┐  ┌────────▼────────┐
   │ S3 Storage │  │ Snowflake DB    │
   │ (Raw Data) │  │ (Transformed)   │
   └────────────┘  └─────────────────┘

4. ORCHESTRATION LAYER
   ┌──────────────────────────────────┐
   │  Apache Airflow (Docker)          │
   │  - DAG: stock_etl_pipeline        │
   │  - Tasks: consume, validate,      │
   │    load, transform, quality-check │
   │  - Scheduling: hourly/daily       │
   │  - Monitoring: logs, alerts       │
   └──────────────┬───────────────────┘

5. TRANSFORMATION LAYER
   ┌──────────────▼───────────────────┐
   │  DBT (Data Build Tool)            │
   │  - Staging: Raw data cleaning     │
   │  - Intermediate: Aggregations     │
   │  - Marts: Business-ready tables   │
   │  - Testing: Schema & data tests   │
   │  - Documentation: Auto-generated  │
   └──────────────┬───────────────────┘

6. DATA QUALITY LAYER
   ┌──────────────▼───────────────────┐
   │  Great Expectations               │
   │  - Schema validation              │
   │  - Null checks                    │
   │  - Range validations              │
   │  - Custom expectations            │
   │  - Data quality dashboards        │
   └──────────────┬───────────────────┘

7. VISUALIZATION LAYER
   ┌──────────────▼───────────────────┐
   │  Tableau Public (Free)            │
   │  - Real-time stock monitor        │
   │  - Historical trends              │
   │  - Data quality metrics           │
   │  - Pipeline performance KPIs      │
   └──────────────────────────────────┘
```

---

## Technology Decisions & Rationale

### Free/Open-Source Choices:

| Component | Choice | Why | Free Tier |
|-----------|--------|-----|-----------|
| **Data Source** | yfinance + Alpha Vantage free tier | Reliable stock data, no auth needed | ✅ Yes |
| **Streaming** | Apache Kafka | Industry standard, easy Docker setup | ✅ Open source |
| **Data Lake** | LocalStack (S3 emulation) | Cost-free local S3 simulation | ✅ Free Docker image |
| **Data Warehouse** | Snowflake | Free trial (30 days, $400 credits) or use local PostgreSQL as backup | ✅ Trial + free tier |
| **Orchestration** | Apache Airflow | Popular, excellent for portfolio | ✅ Open source |
| **Transformation** | DBT Community | Industry standard, free version sufficient | ✅ Free |
| **Data Quality** | Great Expectations | Comprehensive, open source | ✅ Open source |
| **Visualization** | Tableau Public | Free tier, public portfolios | ✅ Free public dashboards |
| **Containerization** | Docker & Docker Compose | Local development, no cloud costs | ✅ Docker Desktop free |

---

## Key Features & Implementation

### 1. Real-Time Data Ingestion
- Python-based Kafka producer fetching stock data every 15 seconds
- Handles multiple stock symbols (configurable)
- Error handling: retry logic, exponential backoff
- Schema validation before publishing

### 2. Streaming & Event Processing
- Kafka topics: `stock_prices`, `stock_volumes`, `stock_metadata`
- Partitioned by stock symbol for parallel processing
- Message format: JSON with timestamp, symbol, price, volume

### 3. Multi-Layer Storage
- **LocalStack S3**: Raw data lake (realistic production pattern)
- **Snowflake**: Transformed, clean data ready for analysis
- Partitioned data: `s3://raw-stock-data/year=2025/month=01/day=15/`

### 4. Orchestration with Airflow
- Main DAG: `stock_etl_pipeline` (hourly)
- Tasks:
  - `kafka_consumer`: Consume messages, write to S3
  - `schema_validation`: Validate incoming data
  - `load_to_snowflake`: Move raw data from S3 to Snowflake staging
  - `run_dbt_models`: Execute DBT transformations
  - `data_quality_checks`: Run Great Expectations
  - `generate_alerts`: Alert if quality checks fail

### 5. Transformation with DBT
- **Staging models**: Clean raw data, handle null/duplicates
- **Intermediate models**: Aggregate by day/hour
- **Mart models**: Final business-ready tables
  - `fact_stock_daily`: Daily OHLCV (Open, High, Low, Close, Volume)
  - `dim_stocks`: Stock master data
- Built-in testing: uniqueness, not-null, accepted values
- Auto-generated documentation

### 6. Data Quality Checks
- Great Expectations checkpoints validate:
  - Schema: column names, data types
  - Data: no nulls in price, positive volumes
  - Ranges: prices within historical bounds
  - Freshness: data not older than 1 hour
- Failed checks trigger Airflow alerts

### 7. Monitoring & Observability
- Prometheus metrics: pipeline duration, data volume, error rates
- Grafana dashboards: real-time pipeline health
- Airflow logs: task-level debugging
- Data lineage: Track data from source to viz

### 8. Visualization
- Tableau Public dashboards:
  - Stock price trends (line chart)
  - Volume analysis (bar chart)
  - Data quality report (metrics)
  - Pipeline run history (KPIs)

---

## Development Environment Setup

### Prerequisites:
- Docker & Docker Compose (free)
- Git
- Python 3.9+
- ~10GB disk space

### One-Command Setup:
```bash
bash scripts/setup-local-env.sh
```

This will:
1. Clone/setup repository
2. Start all Docker containers
3. Initialize Snowflake/S3 buckets
4. Create Kafka topics
5. Deploy Airflow DAGs
6. Run initial data quality checks

---

## Project Milestones

### Phase 1: Foundation (Week 1)
- [ ] Set up Docker Compose with Kafka, Airflow, LocalStack
- [ ] Build Kafka producer for stock data ingestion
- [ ] Create Airflow DAG with basic tasks
- [ ] Write unit tests for producer

### Phase 2: Data Pipeline (Week 2)
- [ ] Implement S3 data lake storage
- [ ] Set up Snowflake connection
- [ ] Build Airflow task: Kafka → S3 → Snowflake
- [ ] Implement schema validation

### Phase 3: Transformation (Week 3)
- [ ] Design DBT models (staging, intermediate, marts)
- [ ] Implement incremental loading in DBT
- [ ] Add DBT tests and documentation
- [ ] Create data lineage

### Phase 4: Quality & Monitoring (Week 4)
- [ ] Integrate Great Expectations
- [ ] Build data quality dashboards
- [ ] Add Prometheus/Grafana monitoring
- [ ] Implement alerting

### Phase 5: Visualization & Polish (Week 5)
- [ ] Create Tableau Public dashboards
- [ ] Write comprehensive documentation
- [ ] Create architecture diagrams
- [ ] Record demo video

---

## Documentation Structure

1. **README.md**: Project overview, quick start, key features
2. **ARCHITECTURE.md**: Detailed technical architecture
3. **docs/setup-guide.md**: Step-by-step local environment setup
4. **docs/data-flow.md**: How data flows through the pipeline
5. **docs/troubleshooting.md**: Common issues & solutions
6. **Code comments**: Inline documentation for complex logic
7. **DBT**: Auto-generated model documentation
8. **Airflow**: DAG visualization and logs

---

## GitHub Best Practices

- **Commits**: Clear, atomic commits with meaningful messages
- **Branches**: Main (production-ready), develop (WIP)
- **Issues**: Track tasks, bugs, feature requests
- **Pull Requests**: Code review process with checklists
- **.gitignore**: Exclude logs, credentials, local data
- **LICENSE**: MIT for portfolio visibility
- **CI/CD**: GitHub Actions for automated testing (future enhancement)

---

## Expected Outcomes for Portfolio

✅ **Skills Demonstrated:**
- End-to-end ETL pipeline architecture
- Real-time data streaming (Kafka)
- Cloud data warehousing (Snowflake)
- Data orchestration (Airflow)
- Data transformation (DBT)
- Data quality & validation (Great Expectations)
- Containerization & DevOps (Docker)
- IaC principles (Docker Compose)
- Monitoring & observability (Prometheus, Grafana)
- SQL, Python, Data modeling

✅ **Portfolio Value:**
- Production-grade code quality
- Comprehensive documentation
- Real data flow (not toy examples)
- Shows problem-solving & best practices
- Demonstrates cloud architecture understanding
- Aligned with current market demand

---

## Next Steps

Once you approve this blueprint, I can:
1. Create the full GitHub repository structure
2. Generate starter code for each component
3. Create Docker setup files
4. Write Airflow DAGs
5. Design DBT models
6. Build Great Expectations configs
7. Create comprehensive README & documentation

**Are you ready to proceed with building this?**
