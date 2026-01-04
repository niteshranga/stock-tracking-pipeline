"""
Real-Time Stock Data Producer
Fetches stock prices from Finnhub and publishes to Kafka topic
Tracks: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, NFLX, UBER, COIN
"""

import os
import json
import logging
from datetime import datetime
import time
from typing import Dict, List

import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinnhubStockProducer:
    """Fetches stock data from Finnhub and publishes to Kafka"""
    
    def __init__(
        self,
        api_key: str,
        bootstrap_servers: str = 'kafka:29092',
        topic: str = 'stock_prices',
        stocks: List[str] = None
    ):
        """
        Initialize Finnhub stock producer
        
        Args:
            api_key: Finnhub API key
            bootstrap_servers: Kafka bootstrap servers
            topic: Kafka topic name
            stocks: List of stock symbols to track
        """
        self.api_key = api_key
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.stocks = stocks or [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA',
            'NVDA', 'META', 'NFLX', 'UBER', 'COIN'
        ]
        self.base_url = 'https://finnhub.io/api/v1'
        
        self.producer = None
        self._initialize_producer()
        logger.info(f"FinnhubStockProducer initialized for stocks: {self.stocks}")
    
    def _initialize_producer(self):
        """Initialize Kafka producer with retry logic"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',
                    retries=3,
                    request_timeout_ms=30000
                )
                logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
                return
            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"Failed to connect to Kafka (attempt {retry_count}/{max_retries}): {e}"
                )
                if retry_count < max_retries:
                    time.sleep(2)
                else:
                    raise Exception(
                        f"Failed to connect to Kafka after {max_retries} attempts"
                    )
    
    def fetch_stock_data(self, symbol: str, retry_count: int = 0, max_retries: int = 3) -> Dict:
        """
        Fetch current stock price for symbol from Finnhub with retry logic
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts
            
        Returns:
            Dict with stock price data or None if failed
        """
        try:
            # Add delay before fetch to respect rate limiting (2 seconds per stock)
            logger.info(f"Waiting 2s before fetching {symbol} (rate limiting)...")
            time.sleep(2)
            
            logger.info(f"Fetching {symbol} from Finnhub...")
            
            # Finnhub quote endpoint
            url = f"{self.base_url}/quote"
            params = {
                'symbol': symbol,
                'token': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we got valid data
            if 'c' not in data or data['c'] == 0:
                logger.warning(f"No valid price data retrieved for {symbol}")
                return None
            
            stock_data = {
                'symbol': symbol,
                'price': float(data['c']),  # current price
                'open': float(data.get('o', 0)),  # open price
                'high': float(data.get('h', 0)),  # high price
                'low': float(data.get('l', 0)),  # low price
                'volume': int(data.get('v', 0)),  # volume
                'timestamp': datetime.now().isoformat(),
                'data_source': 'finnhub'
            }
            
            logger.info(f"✓ Successfully fetched {symbol}: ${stock_data['price']:.2f}")
            return stock_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {symbol} (attempt {retry_count + 1}/{max_retries}): {e}")
            
            # Retry with exponential backoff
            if retry_count < max_retries:
                wait_time = (2 ** retry_count) * 5  # 5s, 10s, 20s
                logger.warning(f"Retrying {symbol} in {wait_time}s...")
                time.sleep(wait_time)
                return self.fetch_stock_data(symbol, retry_count + 1, max_retries)
            
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol} (attempt {retry_count + 1}/{max_retries}): {e}")
            
            # Retry with exponential backoff
            if retry_count < max_retries:
                wait_time = (2 ** retry_count) * 5  # 5s, 10s, 20s
                logger.warning(f"Retrying {symbol} in {wait_time}s...")
                time.sleep(wait_time)
                return self.fetch_stock_data(symbol, retry_count + 1, max_retries)
            
            return None
    
    def publish_message(self, message: Dict) -> bool:
        """
        Publish message to Kafka topic
        
        Args:
            message: Message dict to publish
            
        Returns:
            True if successful, False otherwise
        """
        try:
            future = self.producer.send(
                self.topic,
                value=message
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Published {message['symbol']}: ${message['price']:.2f} "
                f"(partition={record_metadata.partition}, "
                f"offset={record_metadata.offset})"
            )
            return True
        except KafkaError as e:
            logger.error(f"Kafka error publishing message: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def run(self, interval_seconds: int = 60):
        """
        Main loop: fetch and publish stock data at regular intervals
        
        Args:
            interval_seconds: Time between fetches (default 60 seconds)
        """
        logger.info(f"Starting producer loop (interval: {interval_seconds}s)")
        
        try:
            while True:
                fetch_count = 0
                publish_count = 0
                
                for symbol in self.stocks:
                    # Fetch stock data (with built-in 2s delay and retry logic)
                    stock_data = self.fetch_stock_data(symbol)
                    
                    if stock_data:
                        fetch_count += 1
                        
                        # Publish to Kafka
                        if self.publish_message(stock_data):
                            publish_count += 1
                
                logger.info(
                    f"Cycle complete: Fetched {fetch_count}/{len(self.stocks)}, "
                    f"Published {publish_count}/{fetch_count}"
                )
                
                # Wait before next cycle
                logger.info(f"Waiting {interval_seconds}s until next cycle...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Stopping producer (KeyboardInterrupt)")
        except Exception as e:
            logger.error(f"Unexpected error in producer loop: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close Kafka producer connection"""
        if self.producer:
            try:
                self.producer.flush(timeout=10)
                self.producer.close()
                logger.info("Producer closed successfully")
            except Exception as e:
                logger.error(f"Error closing producer: {e}")


def main():
    """Main entry point"""
    # Get config from environment
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        raise ValueError("FINNHUB_API_KEY environment variable not set")
    
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
    topic = os.getenv('KAFKA_TOPIC', 'stock_prices')
    stocks_str = os.getenv('STOCKS', 'AAPL,GOOGL,MSFT,AMZN,TSLA,NVDA,META,NFLX,UBER,COIN')
    fetch_interval = int(os.getenv('FETCH_INTERVAL', '60'))
    
    stocks = [s.strip() for s in stocks_str.split(',')]
    
    logger.info("=" * 80)
    logger.info("STOCK DATA PRODUCER (Finnhub)")
    logger.info("=" * 80)
    logger.info(f"Kafka servers: {bootstrap_servers}")
    logger.info(f"Topic: {topic}")
    logger.info(f"Stocks: {stocks}")
    logger.info(f"Interval: {fetch_interval}s")
    logger.info(f"API: Finnhub")
    logger.info("=" * 80)
    
    # Create and run producer
    producer = FinnhubStockProducer(
        api_key=api_key,
        bootstrap_servers=bootstrap_servers,
        topic=topic,
        stocks=stocks
    )
    
    producer.run(interval_seconds=fetch_interval)


if __name__ == '__main__':
    main()
