{{
    config(
        materialized='table',
        schema='MARTS_STOCKS',
        tags=['mart', 'stock-analytics', 'business']
    )
}}

with daily_aggregates as (
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
        data_points_count
    from {{ ref('int_stock_daily_aggregates') }}
),

with_moving_averages as (
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
        
        -- 7-day moving averages
        avg(daily_close) over (
            partition by symbol 
            order by price_date 
            rows between 6 preceding and current row
        ) as ma_7_day,
        
        -- 30-day moving averages
        avg(daily_close) over (
            partition by symbol 
            order by price_date 
            rows between 29 preceding and current row
        ) as ma_30_day,
        
        -- Price volatility (standard deviation)
        stddev(daily_close) over (
            partition by symbol 
            order by price_date 
            rows between 29 preceding and current row
        ) as volatility_30_day,
        
        -- 52-week high/low (approx 252 trading days)
        max(daily_high) over (
            partition by symbol 
            order by price_date 
            rows between 251 preceding and current row
        ) as high_52_week,
        
        min(daily_low) over (
            partition by symbol 
            order by price_date 
            rows between 251 preceding and current row
        ) as low_52_week
    from daily_aggregates
),

with_technical_indicators as (
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
        ma_7_day,
        ma_30_day,
        volatility_30_day,
        high_52_week,
        low_52_week,
        
        -- RSI-like momentum (price vs 30-day MA)
        case
            when ma_30_day is not null and ma_30_day > 0
            then round(((daily_close - ma_30_day) / ma_30_day) * 100, 2)
            else null
        end as momentum_vs_30ma,
        
        -- Distance from 52-week high/low
        case
            when high_52_week is not null and high_52_week > 0
            then round(((daily_close - high_52_week) / high_52_week) * 100, 2)
            else null
        end as pct_from_52w_high,
        
        case
            when low_52_week is not null and low_52_week > 0
            then round(((daily_close - low_52_week) / low_52_week) * 100, 2)
            else null
        end as pct_from_52w_low,
        
        -- Relative volume
        case
            when avg_volume > 0
            then round(total_volume / avg_volume, 2)
            else null
        end as volume_ratio
    from with_moving_averages
)

select
    md5(concat(symbol, '::', price_date)) as stock_analytics_id,
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
    
    -- Technical indicators
    ma_7_day,
    ma_30_day,
    volatility_30_day,
    high_52_week,
    low_52_week,
    momentum_vs_30ma,
    pct_from_52w_high,
    pct_from_52w_low,
    volume_ratio,
    
    -- Metadata
    current_timestamp() as dbt_created_at,
    current_date() as dbt_run_date
from with_technical_indicators
