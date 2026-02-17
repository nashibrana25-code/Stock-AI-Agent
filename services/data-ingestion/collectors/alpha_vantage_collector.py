"""
Alpha Vantage data collector for ASX stocks
"""
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
import aiohttp
from loguru import logger

from shared.models.financial_models import StockPrice
from shared.config.settings import settings


class AlphaVantageCollector:
    """Collects stock data from Alpha Vantage API"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.alpha_vantage_api_key
        self.source_name = "alpha_vantage"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make API request to Alpha Vantage"""
        if not self.api_key:
            logger.error("Alpha Vantage API key not configured")
            return None
        
        params['apikey'] = self.api_key
        
        try:
            session = await self._get_session()
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for API errors
                    if 'Error Message' in data:
                        logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                        return None
                    if 'Note' in data:
                        logger.warning(f"Alpha Vantage API limit: {data['Note']}")
                        return None
                    
                    return data
                else:
                    logger.error(f"Alpha Vantage API request failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error making Alpha Vantage request: {e}")
            return None
    
    async def get_current_price(self, symbol: str) -> Optional[StockPrice]:
        """Get current/latest price for an ASX stock"""
        # ASX stocks use .AUS suffix on Alpha Vantage
        ticker_symbol = f"{symbol}.AUS" if not symbol.endswith('.AUS') else symbol
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker_symbol
        }
        
        data = await self._make_request(params)
        
        if not data or 'Global Quote' not in data:
            return None
        
        quote = data['Global Quote']
        
        if not quote or '05. price' not in quote:
            logger.warning(f"No quote data for {symbol}")
            return None
        
        try:
            return StockPrice(
                symbol=symbol.replace('.AUS', ''),
                source=self.source_name,
                timestamp=datetime.utcnow(),
                open=Decimal(quote.get('02. open', quote['05. price'])),
                high=Decimal(quote.get('03. high', quote['05. price'])),
                low=Decimal(quote.get('04. low', quote['05. price'])),
                close=Decimal(quote['05. price']),
                volume=int(quote.get('06. volume', 0)),
                adjusted_close=Decimal(quote.get('08. previous close', quote['05. price']))
            )
        except Exception as e:
            logger.error(f"Error parsing Alpha Vantage data for {symbol}: {e}")
            return None
    
    async def get_intraday_prices(
        self, 
        symbol: str, 
        interval: str = "5min"
    ) -> List[StockPrice]:
        """Get intraday price data"""
        ticker_symbol = f"{symbol}.AUS" if not symbol.endswith('.AUS') else symbol
        
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': ticker_symbol,
            'interval': interval,
            'outputsize': 'full'
        }
        
        data = await self._make_request(params)
        
        if not data:
            return []
        
        # Find the time series key
        ts_key = f'Time Series ({interval})'
        if ts_key not in data:
            logger.warning(f"No intraday data for {symbol}")
            return []
        
        prices = []
        time_series = data[ts_key]
        
        try:
            for timestamp_str, values in time_series.items():
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                prices.append(StockPrice(
                    symbol=symbol.replace('.AUS', ''),
                    source=self.source_name,
                    timestamp=timestamp,
                    open=Decimal(values['1. open']),
                    high=Decimal(values['2. high']),
                    low=Decimal(values['3. low']),
                    close=Decimal(values['4. close']),
                    volume=int(values['5. volume'])
                ))
        except Exception as e:
            logger.error(f"Error parsing intraday data for {symbol}: {e}")
        
        return prices
    
    async def get_daily_prices(
        self, 
        symbol: str, 
        outputsize: str = "compact"
    ) -> List[StockPrice]:
        """Get daily historical prices"""
        ticker_symbol = f"{symbol}.AUS" if not symbol.endswith('.AUS') else symbol
        
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': ticker_symbol,
            'outputsize': outputsize  # compact = last 100 days, full = 20+ years
        }
        
        data = await self._make_request(params)
        
        if not data or 'Time Series (Daily)' not in data:
            return []
        
        prices = []
        time_series = data['Time Series (Daily)']
        
        try:
            for date_str, values in time_series.items():
                timestamp = datetime.strptime(date_str, '%Y-%m-%d')
                
                prices.append(StockPrice(
                    symbol=symbol.replace('.AUS', ''),
                    source=self.source_name,
                    timestamp=timestamp,
                    open=Decimal(values['1. open']),
                    high=Decimal(values['2. high']),
                    low=Decimal(values['3. low']),
                    close=Decimal(values['4. close']),
                    volume=int(values['6. volume']),
                    adjusted_close=Decimal(values['5. adjusted close'])
                ))
        except Exception as e:
            logger.error(f"Error parsing daily data for {symbol}: {e}")
        
        return prices
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[StockPrice]]:
        """Get current prices for multiple stocks with rate limiting"""
        results = {}
        
        # Alpha Vantage has rate limits (5 API requests per minute for free tier)
        # Add delay between requests
        for symbol in symbols:
            results[symbol] = await self.get_current_price(symbol)
            await asyncio.sleep(12)  # 5 requests per minute = 12 seconds per request
        
        return results
