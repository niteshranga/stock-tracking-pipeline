"""
Airflow DAG: Stock Data Ingestion to Snowflake
Consumes stock price messages from Kafka and inserts into Snowflake
Runs every 5 minutes
Credentials loaded from environment variables (secrets.env)
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict
import json
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.utils.task_group import TaskGroup
from airflow.exceptions import AirflowException

from kafka import KafkaConsumer
from kafka.errors import KafkaError
import snowflake.connector


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Load Credentials from Environment Variables
# ============================================================================

def get_snowflake_credentials():
    """
    Load Snowflake credentials from environment variables
    These should be set in secrets.env and loaded by docker-compose
    """
    credentials = {
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA'),
    }
    
    # Validate required credentials are set
    if not credentials['password']:
        raise AirflowException(
            "SNOWFLAKE_PASSWORD environment variable not set. "
            "Please set it in secrets.env"
        )
    
    logger.info(f"Loaded Snowflake credentials from environment")
    logger.info(f"Account: {credentials['account']}")
    logger.info(f"User: {credentials['user']}")
    logger.info(f"Database: {credentials['database']}")
    logger.info(f"Schema: {credentials['schema']}")
    
    return credentials


# ============================================================================
# DAG Configuration
# ============================================================================

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email': ['admin@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'stock_data_ingestion_snowflake',
    default_args=default_args,
    description='Ingest real-time stock prices from Kafka to Snowflake',
    schedule_interval='*/5 * * * *',  # Every 5 minutes
    catchup=False,
    tags=['stock-pipeline', 'ingestion', 'real-time', 'snowflake'],
)


# ============================================================================
# Task Functions
# ============================================================================

def consume_kafka_messages(
    bootstrap_servers: str = 'kafka:29092',
    topic: str = 'stock_prices',
    timeout_ms: int = 5000,
    max_records: int = 100,
    **context
) -> List[Dict]:
    """
    Consume messages from Kafka topic
    
    Args:
        bootstrap_servers: Kafka bootstrap servers
        topic: Topic name
        timeout_ms: Consumer timeout
        max_records: Max records to fetch
        
    Returns:
        List of messages
    """
    logger.info(f"Starting Kafka consumer: {bootstrap_servers}, topic: {topic}")
    
    messages = []
    
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='airflow-stock-ingestion-snowflake',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=timeout_ms,
            session_timeout_ms=30000,
            request_timeout_ms=60000
        )
        
        logger.info(f"Connected to Kafka consumer group")
        
        # Consume messages
        for message in consumer:
            messages.append(message.value)
            logger.debug(f"Consumed message: {message.value['symbol']} @ ${message.value['price']}")
            
            if len(messages) >= max_records:
                logger.info(f"Reached max records limit ({max_records})")
                break
        
        consumer.close()
        logger.info(f"Consumed {len(messages)} messages from Kafka")
        
    except KafkaError as e:
        logger.error(f"Kafka error during consumption: {e}")
        raise AirflowException(f"Failed to consume from Kafka: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during message consumption: {e}")
        raise AirflowException(f"Unexpected error consuming messages: {e}")
    
    # Push messages to XCom for next task
    context['task_instance'].xcom_push(key='messages', value=messages)
    logger.info(f"Pushed {len(messages)} messages to XCom")
    
    return messages


def insert_into_snowflake(
    snowflake_account: str = None,
    snowflake_user: str = None,
    snowflake_password: str = None,
    snowflake_warehouse: str = None,
    snowflake_database: str = None,
    snowflake_schema: str = None,
    **context
) -> Dict:
    """
    Insert consumed messages into Snowflake
    Uses credentials from environment variables if not provided
    
    Args:
        snowflake_account: Snowflake account ID (optional, uses env var if not provided)
        snowflake_user: Snowflake username (optional, uses env var if not provided)
        snowflake_password: Snowflake password (optional, uses env var if not provided)
        snowflake_warehouse: Warehouse name (optional, uses env var if not provided)
        snowflake_database: Database name (optional, uses env var if not provided)
        snowflake_schema: Schema name (optional, uses env var if not provided
        
    Returns:
        Dict with insertion statistics
    """
    logger.info("Starting Snowflake insert task")
    
    # Load credentials from environment if not provided
    if any(arg is None for arg in [
        snowflake_account, snowflake_user, snowflake_password,
        snowflake_warehouse, snowflake_database, snowflake_schema
    ]):
        creds = get_snowflake_credentials()
        snowflake_account = snowflake_account or creds['account']
        snowflake_user = snowflake_user or creds['user']
        snowflake_password = snowflake_password or creds['password']
        snowflake_warehouse = snowflake_warehouse or creds['warehouse']
        snowflake_database = snowflake_database or creds['database']
        snowflake_schema = snowflake_schema or creds['schema']
    
    # Get messages from XCom
    ti = context['task_instance']
    messages = ti.xcom_pull(task_ids='consume_kafka', key='messages')
    
    if not messages:
        logger.info("No messages to insert")
        return {'inserted': 0, 'failed': 0}
    
    logger.info(f"Retrieved {len(messages)} messages from XCom")
    
    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            account=snowflake_account,
            user=snowflake_user,
            password=snowflake_password,
            warehouse=snowflake_warehouse,
            database=snowflake_database,
            schema=snowflake_schema
        )
        
        cursor = conn.cursor()
        logger.info(f"Connected to Snowflake: {snowflake_user}@{snowflake_account}/{snowflake_database}.{snowflake_schema}")
        
        # Create table if not exists
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS STOCK_PRICES (
            ID VARCHAR,
            SYMBOL VARCHAR(10) NOT NULL,
            PRICE DECIMAL(10, 2) NOT NULL,
            VOLUME BIGINT NOT NULL,
            TIMESTAMP TIMESTAMP_NTZ NOT NULL,
            FETCHED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            DATA_SOURCE VARCHAR(50),
            HIGH DECIMAL(10, 2),
            LOW DECIMAL(10, 2),
            OPEN DECIMAL(10, 2),
            UNIQUE(SYMBOL, TIMESTAMP)
        )
        """
        cursor.execute(create_table_sql)
        logger.info("Table created or already exists")
        
        # Prepare data for insertion
        insert_count = 0
        skip_count = 0
        
        for message in messages:
            try:
                # Prepare row
                symbol = message.get('symbol')
                price = float(message.get('price', 0))
                volume = int(message.get('volume', 0))
                timestamp = message.get('timestamp')
                data_source = message.get('data_source', 'unknown')
                high = message.get('high')
                low = message.get('low')
                open_price = message.get('open')
                
                # Insert row
                insert_query = """
                    INSERT INTO STOCK_PRICES 
                    (SYMBOL, PRICE, VOLUME, TIMESTAMP, DATA_SOURCE, HIGH, LOW, OPEN)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    symbol, price, volume, timestamp, 
                    data_source, high, low, open_price
                ))
                insert_count += 1
                logger.debug(f"Inserted: {symbol} @ ${price}")
                
            except snowflake.connector.errors.DatabaseError as e:
                if 'UNIQUE constraint violated' in str(e):
                    logger.debug(f"Duplicate entry skipped: {message.get('symbol')}")
                    skip_count += 1
                else:
                    logger.error(f"Database error inserting message {message}: {e}")
                    skip_count += 1
            except Exception as e:
                logger.error(f"Error inserting message {message}: {e}")
                skip_count += 1
        
        # Commit transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(
            f"Snowflake insert complete: {insert_count} inserted, {skip_count} skipped"
        )
        
        # Push statistics to XCom
        stats = {'inserted': insert_count, 'skipped': skip_count}
        ti.xcom_push(key='insert_stats', value=stats)
        
        return stats
        
    except snowflake.connector.errors.ProgrammingError as e:
        logger.error(f"Snowflake programming error: {e}")
        raise AirflowException(f"Failed to execute Snowflake query: {e}")
    except snowflake.connector.errors.OperationalError as e:
        logger.error(f"Snowflake connection error: {e}")
        raise AirflowException(f"Failed to connect to Snowflake: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during Snowflake insert: {e}")
        raise AirflowException(f"Failed to insert data: {e}")


def log_ingestion_stats(**context) -> None:
    """
    Log ingestion statistics
    """
    ti = context['task_instance']
    
    consumed_count = len(ti.xcom_pull(task_ids='consume_kafka', key='messages') or [])
    insert_stats = ti.xcom_pull(task_ids='insert_snowflake', key='insert_stats') or {}
    
    logger.info("=" * 80)
    logger.info("SNOWFLAKE INGESTION STATISTICS")
    logger.info("=" * 80)
    logger.info(f"Messages consumed: {consumed_count}")
    logger.info(f"Messages inserted: {insert_stats.get('inserted', 0)}")
    logger.info(f"Messages skipped: {insert_stats.get('skipped', 0)}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80)


# ============================================================================
# DAG Tasks
# ============================================================================

# Task 1: Consume from Kafka
consume_kafka = PythonOperator(
    task_id='consume_kafka',
    python_callable=consume_kafka_messages,
    op_kwargs={
        'bootstrap_servers': 'kafka:29092',
        'topic': 'stock_prices',
        'timeout_ms': 10000,
        'max_records': 100
    },
    provide_context=True,
    dag=dag,
)

# Task 2: Insert into Snowflake
# Note: Credentials are loaded from environment variables
insert_snowflake = PythonOperator(
    task_id='insert_snowflake',
    python_callable=insert_into_snowflake,
    op_kwargs={
        # Leave these as None - will load from environment variables
        'snowflake_account': None,
        'snowflake_user': None,
        'snowflake_password': None,
        'snowflake_warehouse': None,
        'snowflake_database': None,
        'snowflake_schema': None,
    },
    provide_context=True,
    dag=dag,
)

# Task 3: Log statistics
log_stats = PythonOperator(
    task_id='log_stats',
    python_callable=log_ingestion_stats,
    provide_context=True,
    dag=dag,
)

# ============================================================================
# Task Dependencies
# ============================================================================

consume_kafka >> insert_snowflake >> log_stats
