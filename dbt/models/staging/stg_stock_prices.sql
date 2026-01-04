{{
    config(
        materialized='table',
        schema='STG_STOCKS',
        tags=['staging', 'stock-prices']
    )
}}

with source_data as (
    select
        id,
        symbol,
        price,
        volume,
        timestamp,
        fetched_at,
        data_source,
        high,
        low,
        open,
        cast(timestamp as date) as price_date,
        extract(hour from timestamp) as price_hour,
        datediff(second, timestamp, fetched_at) as ingest_lag_seconds
    from STOCKS_FIN.RAW_STOCKS.STOCK_PRICES
),

data_quality_checks as (
    select
        *,
        case 
            when price <= 0 then false
            when volume < 0 then false
            when high < low then false
            when open < 0 then false
            else true
        end as is_valid_record,
        
        case
            when abs(price - lag(price) over (partition by symbol order by timestamp)) 
                 / lag(price) over (partition by symbol order by timestamp) > 0.20
            then true
            else false
        end as is_price_spike
    from source_data
)

select
    id,
    symbol,
    price,
    volume,
    timestamp,
    fetched_at,
    data_source,
    high,
    low,
    open,
    price_date,
    price_hour,
    ingest_lag_seconds,
    is_valid_record,
    is_price_spike,
    current_timestamp() as dbt_created_at,
    current_timestamp() as dbt_updated_at
from data_quality_checks
