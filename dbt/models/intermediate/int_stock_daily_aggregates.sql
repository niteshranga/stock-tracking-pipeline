{{
    config(
        materialized='table',
        schema='INT_STOCKS',
        tags=['intermediate', 'stock-analysis']
    )
}}

with staged_data as (
    select
        symbol,
        price,
        volume,
        timestamp,
        high,
        low,
        open,
        price_date,
        is_valid_record
    from {{ ref('stg_stock_prices') }}
    where is_valid_record = true
),

daily_aggregates as (
    select
        symbol,
        price_date,
        
        -- Daily OHLC
        first_value(open) over (
            partition by symbol, price_date 
            order by timestamp 
            rows between unbounded preceding and unbounded following
        ) as daily_open,
        max(high) over (
            partition by symbol, price_date
        ) as daily_high,
        min(low) over (
            partition by symbol, price_date
        ) as daily_low,
        last_value(price) over (
            partition by symbol, price_date 
            order by timestamp 
            rows between unbounded preceding and unbounded following
        ) as daily_close,
        
        -- Volume metrics
        sum(volume) over (
            partition by symbol, price_date
        ) as total_volume,
        avg(volume) over (
            partition by symbol, price_date
        ) as avg_volume,
        
        -- Price movements
        round(
            ((last_value(price) over (
                partition by symbol, price_date 
                order by timestamp 
                rows between unbounded preceding and unbounded following
            ) - first_value(open) over (
                partition by symbol, price_date 
                order by timestamp 
                rows between unbounded preceding and unbounded following
            )) / first_value(open) over (
                partition by symbol, price_date 
                order by timestamp 
                rows between unbounded preceding and unbounded following
            )) * 100,
            2
        ) as daily_change_pct,
        
        -- Count data points
        count(*) over (
            partition by symbol, price_date
        ) as data_points_count,
        
        -- Row number for deduplication
        row_number() over (
            partition by symbol, price_date 
            order by timestamp desc
        ) as rn
    from staged_data
),

deduped_data as (
    select
        symbol,
        price_date,
        daily_open,
        daily_high,
        daily_low,
        daily_close,
        total_volume,
        avg_volume,
        daily_change_pct,
        data_points_count,
        current_timestamp() as dbt_created_at
    from daily_aggregates
    where rn = 1
)

select
    md5(concat(symbol, '::', price_date)) as stock_day_id,
    symbol,
    price_date,
    daily_open,
    daily_high,
    daily_low,
    daily_close,
    total_volume,
    avg_volume,
    daily_change_pct,
    data_points_count,
    dbt_created_at
from deduped_data
