-- PostgreSQL Initialization Script
-- Creates databases and users for Airflow, DBT, and application data

-- Create DBT database
CREATE DATABASE dbt_dev
  WITH
    ENCODING 'UTF8'
    TEMPLATE 'template0'
    LC_COLLATE 'C'
    LC_CTYPE 'C';

-- Create DBT user
CREATE USER dbt_user WITH PASSWORD 'dbt_password';

-- Grant privileges to dbt_user on dbt_dev database
GRANT ALL PRIVILEGES ON DATABASE dbt_dev TO dbt_user;

-- Connect to dbt_dev and set schema privileges
\c dbt_dev

-- Create schema for staging data
CREATE SCHEMA IF NOT EXISTS raw_stocks;
CREATE SCHEMA IF NOT EXISTS stg_stocks;
CREATE SCHEMA IF NOT EXISTS int_stocks;
CREATE SCHEMA IF NOT EXISTS marts_stocks;

-- Grant privileges on schemas
GRANT ALL PRIVILEGES ON SCHEMA raw_stocks, stg_stocks, int_stocks, marts_stocks TO dbt_user;

-- Set default privileges for future tables/views
ALTER DEFAULT PRIVILEGES IN SCHEMA raw_stocks GRANT ALL ON TABLES TO dbt_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA stg_stocks GRANT ALL ON TABLES TO dbt_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA int_stocks GRANT ALL ON TABLES TO dbt_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA marts_stocks GRANT ALL ON TABLES TO dbt_user;

-- Grant privileges on existing tables (if any)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw_stocks TO dbt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA stg_stocks TO dbt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA int_stocks TO dbt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA marts_stocks TO dbt_user;

-- Create extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables for storing raw stock data (for demonstration)
CREATE TABLE IF NOT EXISTS raw_stocks.stock_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50),
    CONSTRAINT stock_prices_unique UNIQUE(symbol, timestamp)
);

-- Create index for common queries
CREATE INDEX idx_stock_prices_symbol_timestamp 
  ON raw_stocks.stock_prices(symbol, timestamp DESC);
CREATE INDEX idx_stock_prices_fetched_at 
  ON raw_stocks.stock_prices(fetched_at DESC);

-- Grant privileges on tables to dbt_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw_stocks TO dbt_user;

-- Grant sequence privileges (for auto-increment IDs)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw_stocks TO dbt_user;

-- Create table for tracking data pipeline runs
CREATE TABLE IF NOT EXISTS raw_stocks.pipeline_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dag_id VARCHAR(255) NOT NULL,
    run_date TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    records_processed BIGINT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pipeline_runs_run_date 
  ON raw_stocks.pipeline_runs(run_date DESC);
CREATE INDEX idx_pipeline_runs_status 
  ON raw_stocks.pipeline_runs(status);

-- Grant privileges on pipeline_runs table
GRANT ALL PRIVILEGES ON raw_stocks.pipeline_runs TO dbt_user;

-- Create table for data quality metrics
CREATE TABLE IF NOT EXISTS raw_stocks.data_quality_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    check_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    records_checked BIGINT,
    records_failed BIGINT,
    failure_rate DECIMAL(5, 2),
    check_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_details TEXT
);

CREATE INDEX idx_data_quality_metrics_timestamp 
  ON raw_stocks.data_quality_metrics(check_timestamp DESC);
CREATE INDEX idx_data_quality_metrics_status 
  ON raw_stocks.data_quality_metrics(status);

-- Grant privileges on data_quality_metrics table
GRANT ALL PRIVILEGES ON raw_stocks.data_quality_metrics TO dbt_user;

-- Note: The 'airflow' database is created by default with postgres user
-- Airflow will use this database for its metadata storage
-- No additional configuration needed for Airflow database in this script

-- Summary
\echo '========================================='
\echo 'PostgreSQL Initialization Complete!'
\echo '========================================='
\echo 'Databases created:'
\echo '  - airflow (for Airflow metadata)'
\echo '  - dbt_dev (for DBT models and transformations)'
\echo ''
\echo 'Users created:'
\echo '  - airflow (default Airflow user)'
\echo '  - dbt_user (for DBT operations)'
\echo ''
\echo 'Schemas created in dbt_dev:'
\echo '  - raw_stocks (raw data from ingestion)'
\echo '  - stg_stocks (staging/cleaned data)'
\echo '  - int_stocks (intermediate transformations)'
\echo '  - marts_stocks (final business-ready tables)'
\echo ''
\echo 'Tables created:'
\echo '  - raw_stocks.stock_prices (raw stock data)'
\echo '  - raw_stocks.pipeline_runs (pipeline execution tracking)'
\echo '  - raw_stocks.data_quality_metrics (data quality tracking)'
\echo '========================================='
