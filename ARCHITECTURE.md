# System Architecture

## Overview

The Real-Time Stock Tracking Pipeline is a **modern data stack** that ingests, processes, and visualizes stock market data in real-time.

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Finnhub API  ──(REST)──>  Stock Producer  ──(JSON)──>  Kafka    │
│  (Every 60s)                (Docker)                   (Topic:     │
│  10 stocks                  Rate Limited              stock_prices)│
│                             Retry Logic                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│              Airflow DAG (Every 5 minutes)                         │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ consume_kafka    │─>│ insert_snowflake │─>│   log_stats     │ │
│  │ Read from topic  │  │ Write to DB      │  │ Record metrics  │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DATA WAREHOUSE LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SNOWFLAKE (Cloud Data Warehouse)                                 │
│  ├── Database: STOCKS_FIN                                          │
│  │                                                                 │
│  └── RAW_STOCKS (Raw ingestion layer)                             │
│      └── STOCK_PRICES (1000+ records)                             │
│          - symbol, price, volume, timestamp                        │
│          - high, low, open, data_source                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  TRANSFORMATION LAYER (DBT)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STAGING LAYER (STG_STOCKS)                                        │
│  └── stg_stock_prices                                              │
│      - Data quality checks                                          │
│      - Price validation (price > 0)                                 │
│      - Spike detection (>20% change)                                │
│      - Date/hour extraction                                         │
│                          │                                          │
│                          ▼                                          │
│                                                                     │
│  INTERMEDIATE LAYER (INT_STOCKS)                                   │
│  └── int_stock_daily_aggregates                                    │
│      - Daily OHLC (Open, High, Low, Close)                         │
│      - Volume statistics                                            │
│      - Daily change percentage                                      │
│      - Deduplication by date                                        │
│                          │                                          │
│                          ▼                                          │
│                                                                     │
│  MARTS LAYER (MARTS_STOCKS)                                        │
│  └── stock_analytics                                               │
│      - 7-day moving average                                         │
│      - 30-day moving average                                        │
│      - 30-day volatility                                            │
│      - 52-week highs/lows                                           │
│      - Technical indicators                                         │
│      - Momentum metrics                                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS & VISUALIZATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Google Looker Studio Dashboard                                    │
│  ├── Stock Price Trends (Time Series)                              │
│  ├── Performance Table                                              │
│  ├── Interactive Filters                                            │
│  │   - By Symbol                                                    │
│  │   - By Date Range                                                │
│  └── Auto-refresh (every 5 minutes)                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Data Ingestion (Stock Producer)

**Purpose:** Fetch stock prices from Finnhub API

**Technology:** Python + Kafka Producer

**Details:**
- Fetches 10 stocks every 60 seconds
- Rate limiting: 2 seconds between requests
- Exponential backoff retry (5s, 10s, 20s)
- Publishes JSON to Kafka topic
- Error handling: logs failures, continues

**Configuration:**
```
STOCKS=AAPL,GOOGL,MSFT,AMZN,TSLA,NVDA,META,NFLX,UBER,COIN
FETCH_INTERVAL=60 seconds
FINNHUB_API_KEY=required
```

---

### 2. Message Queue (Apache Kafka)

**Purpose:** Stream stock price messages

**Technology:** Kafka 7.4.0

**Details:**
- Topic: `stock_prices`
- Partitions: 1
- Replication Factor: 1
- Retention: 24 hours
- Format: JSON

**Message Schema:**
```json
{
  "symbol": "AAPL",
  "price": 150.25,
  "high": 151.00,
  "low": 149.50,
  "open": 149.75,
  "volume": 1000000,
  "timestamp": "2025-01-04T14:30:00Z",
  "data_source": "finnhub"
}
```

---

### 3. Orchestration (Apache Airflow)

**Purpose:** Schedule and execute data pipeline

**Technology:** Airflow 2.7.3

**DAG:** `stock_data_ingestion_snowflake`

**Schedule:** Every 5 minutes

**Tasks:**
1. **consume_kafka** - Read from Kafka topic
   - Consumer group: `airflow-stock-ingestion-snowflake`
   - Timeout: 10 seconds
   - Max records: 100

2. **insert_snowflake** - Write to Snowflake
   - Creates table if not exists
   - Handles duplicates
   - Logs statistics

3. **log_stats** - Log metrics
   - Records consumed count
   - Records inserted count
   - Records skipped count

**Error Handling:**
- Retries: 2 attempts
- Retry delay: 5 minutes
- On failure: Logs error, continues next cycle

---

### 4. Data Warehouse (Snowflake)

**Purpose:** Store all data (raw, staged, transformed)

**Technology:** Snowflake Cloud Data Warehouse

**Database:** `STOCKS_FIN`

**Schemas:**
```
STOCKS_FIN/
├── RAW_STOCKS (Raw ingestion layer)
│   └── STOCK_PRICES (1000+ records)
│
├── STG_STOCKS (Staging layer)
│   └── STG_STOCK_PRICES (cleaned data)
│
├── INT_STOCKS (Intermediate layer)
│   └── INT_STOCK_DAILY_AGGREGATES (daily metrics)
│
└── MARTS_STOCKS (Analytics layer)
    └── STOCK_ANALYTICS (ready for dashboards)
```

**Table Details:**

**RAW_STOCKS.STOCK_PRICES:**
- Columns: symbol, price, volume, timestamp, high, low, open, data_source
- Primary Key: (symbol, timestamp)
- Size: ~1000+ rows

**MARTS_STOCKS.STOCK_ANALYTICS:**
- Columns: symbol, price_date, daily_close, ma_7_day, ma_30_day, volatility_30_day, etc.
- Size: ~100+ rows
- Used by: Looker Studio dashboards

---

### 5. Data Transformation (DBT)

**Purpose:** Transform raw data into analytics tables

**Technology:** DBT 1.7.0

**Three-Layer Architecture:**

**Layer 1: Staging (STG_STOCKS)**
- Input: RAW_STOCKS.STOCK_PRICES
- Transformations:
  - Data quality validation
  - Price spike detection
  - Date/hour extraction
  - Ingest lag calculation
- Output: STG_STOCK_PRICES (cleaned data)

**Layer 2: Intermediate (INT_STOCKS)**
- Input: STG_STOCKS.STG_STOCK_PRICES
- Transformations:
  - Daily OHLC aggregation
  - Volume statistics
  - Daily change calculations
  - Deduplication
- Output: INT_STOCK_DAILY_AGGREGATES (daily metrics)

**Layer 3: Marts (MARTS_STOCKS)**
- Input: INT_STOCKS.INT_STOCK_DAILY_AGGREGATES
- Transformations:
  - Moving averages (7-day, 30-day)
  - Volatility (30-day standard deviation)
  - 52-week highs/lows
  - Technical indicators
- Output: STOCK_ANALYTICS (analytics-ready)

---

### 6. Visualization (Google Looker Studio)

**Purpose:** Interactive dashboards and reports

**Technology:** Google Looker Studio (FREE)

**Dashboards:**
1. **Stock Analytics Dashboard**
   - Chart 1: Stock Price Trends (Time Series)
   - Chart 2: Performance Table (All metrics)

**Filters:**
- Symbol dropdown (select specific stock)
- Date range slider (filter by date)

**Auto-refresh:** Every 5 minutes (syncs with Airflow)

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Message Queue** | Apache Kafka | 7.4.0 | Stream processing |
| **Orchestration** | Apache Airflow | 2.7.3 | DAG scheduling |
| **Data Warehouse** | Snowflake | Cloud | Storage & analytics |
| **Transformation** | DBT | 1.7.0 | ELT workflow |
| **Visualization** | Looker Studio | FREE | Dashboards |
| **Containerization** | Docker | Latest | Infrastructure |
| **Monitoring** | Prometheus & Grafana | Latest | System health |
| **API** | Finnhub | v1 | Stock data source |
| **Message Format** | JSON | - | Data serialization |
| **Language** | Python | 3.11 | Code |

---

## Data Quality

### Validation Rules (Staging Layer)

```python
if price <= 0:
    is_valid = False
if volume < 0:
    is_valid = False
if high < low:
    is_valid = False
if open < 0:
    is_valid = False
```

### Anomaly Detection

```python
price_change_pct = (current_price - previous_price) / previous_price * 100
if price_change_pct > 20%:
    is_price_spike = True  # Flag for review
```

---

## Performance Characteristics

### Latency
- API Fetch: <1 second per stock
- Kafka Publish: <1 second
- Airflow DAG: ~10-15 seconds total
- DBT Run: ~5-10 seconds total
- Looker Refresh: ~2-3 seconds

### Throughput
- Messages/minute: ~167 (10 stocks × 1 per 60s)
- Daily records: ~1000+
- Monthly records: ~30,000+
- Storage needed: <100MB

### Availability
- Target: 99.5% uptime
- Failure handling: Automatic retries
- Data redundancy: Snowflake backup

---

## Security Architecture

### Data Protection

```
Secrets Layer:
└── secrets.env (local only, git-ignored)
    ├── SNOWFLAKE credentials
    ├── FINNHUB API key
    └── Never committed to GitHub

Environment Variable Layer:
└── docker-compose.yml references ${VAR_NAME}
    ├── Loads from secrets.env
    └── No hardcoded credentials

Application Layer:
└── Code uses os.getenv() safely
    ├── Reads from environment
    └── Credentials never logged
```

### Access Control

- Snowflake Role: ACCOUNTADMIN (full access)
- DBT Profile: Uses environment variables
- GitHub: Example files only (no secrets)

---

## Deployment Architecture

### Local Development
```
Docker Compose
├── Zookeeper
├── Kafka
├── PostgreSQL
├── Airflow (Webserver + Scheduler)
├── Stock Producer
└── Monitoring (Prometheus + Grafana)
```

### Production Considerations

1. **Scaling:** Kafka partitions, Airflow parallelism
2. **Monitoring:** Prometheus metrics, Grafana dashboards
3. **Backup:** Snowflake automatic backups
4. **High Availability:** Multiple Airflow executors
5. **Security:** Encrypted credentials, VPC endpoints

---

## Integration Points

### External Services
1. **Finnhub API** → Stock data source
2. **Snowflake** → Cloud data warehouse
3. **Google Looker Studio** → Visualization

### Internal Communication
1. **Stock Producer** → Kafka (JSON)
2. **Airflow** → Kafka (consume)
3. **Airflow** → Snowflake (insert)
4. **DBT** → Snowflake (transform)
5. **Looker** → Snowflake (query)

---

## Future Enhancements

1. **Real-time Alerting**
   - PagerDuty integration
   - Slack notifications
   - Email alerts

2. **Advanced Analytics**
   - Machine learning models
   - Predictive analytics
   - Sentiment analysis

3. **Scaling**
   - Kafka partitions
   - Airflow distributed execution
   - Snowflake clustering

4. **Data Quality**
   - Great Expectations
   - dbt tests
   - Anomaly detection

---

## Monitoring & Observability

### Metrics Collected
- Message throughput (msg/sec)
- Airflow DAG runtime
- Snowflake query performance
- Data freshness
- Error rates

### Dashboards
- Grafana system health
- Airflow DAG status
- Looker Studio analytics

---

**Last Updated:** January 2025
**Version:** 1.0.0
**Status:** Production Ready
