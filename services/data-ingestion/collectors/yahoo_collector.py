"""
Yahoo Finance data collector for ASX stocks
"""
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict
import yfinance as yf
from loguru import logger

from shared.models.financial_models import StockPrice, StockInfo


class YahooFinanceCollector:
    """Collects stock data from Yahoo Finance"""
    
    def __init__(self):
        self.source_name = "yahoo_finance"
    
    async def get_current_price(self, symbol: str) -> Optional[StockPrice]:
        """Get current price for an ASX stock"""
        try:
            # ASX stocks use .AX suffix on Yahoo Finance
            ticker_symbol = f"{symbol}.AX" if not symbol.endswith('.AX') else symbol
            ticker = yf.Ticker(ticker_symbol)
            
            # Get current data
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                logger.warning(f"No price data available for {symbol}")
                return None
            
            return StockPrice(
                symbol=symbol.replace('.AX', ''),
                source=self.source_name,
                timestamp=datetime.utcnow(),
                open=Decimal(str(info.get('regularMarketOpen', info['regularMarketPrice']))),
                high=Decimal(str(info.get('dayHigh', info['regularMarketPrice']))),
                low=Decimal(str(info.get('dayLow', info['regularMarketPrice']))),
                close=Decimal(str(info['regularMarketPrice'])),
                volume=int(info.get('volume', 0)),
                adjusted_close=Decimal(str(info['regularMarketPrice']))
            )
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    async def get_historical_prices(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: str = "1d"
    ) -> List[StockPrice]:
        """Get historical price data"""
        try:
            ticker_symbol = f"{symbol}.AX" if not symbol.endswith('.AX') else symbol
            ticker = yf.Ticker(ticker_symbol)
            
            # Download historical data
            hist = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if hist.empty:
                logger.warning(f"No historical data for {symbol}")
                return []
            
            prices = []
            for index, row in hist.iterrows():
                prices.append(StockPrice(
                    symbol=symbol.replace('.AX', ''),
                    source=self.source_name,
                    timestamp=index.to_pydatetime(),
                    open=Decimal(str(row['Open'])),
                    high=Decimal(str(row['High'])),
                    low=Decimal(str(row['Low'])),
                    close=Decimal(str(row['Close'])),
                    volume=int(row['Volume']),
                    adjusted_close=Decimal(str(row['Close']))
                ))
            
            return prices
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []
    
    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Get company information"""
        try:
            ticker_symbol = f"{symbol}.AX" if not symbol.endswith('.AX') else symbol
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            if not info:
                return None
            
            return StockInfo(
                symbol=symbol.replace('.AX', ''),
                company_name=info.get('longName', info.get('shortName', symbol)),
                sector=info.get('sector', 'Unknown'),
                industry=info.get('industry', 'Unknown'),
                market_cap=Decimal(str(info.get('marketCap', 0))) if info.get('marketCap') else None,
                pe_ratio=Decimal(str(info.get('trailingPE', 0))) if info.get('trailingPE') else None,
                dividend_yield=Decimal(str(info.get('dividendYield', 0))) if info.get('dividendYield') else None,
                beta=Decimal(str(info.get('beta', 1.0))) if info.get('beta') else None,
                description=info.get('longBusinessSummary'),
                website=info.get('website')
            )
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return None
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[StockPrice]]:
        """Get current prices for multiple stocks concurrently"""
        tasks = [self.get_current_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        return dict(zip(symbols, results))
    
    async def search_asx_stocks(self, query: str) -> List[str]:
        """Search for ASX stocks (limited functionality in yfinance)"""
        # This is a basic implementation - would need enhancement
        # In production, you'd use ASX API or maintain a database of ASX tickers
        try:
            # Try to fetch the ticker
            ticker = yf.Ticker(f"{query}.AX")
            info = ticker.info
            if info and 'symbol' in info:
                return [query]
            return []
        except:
            return []


# Commonly traded ASX stocks for initial testing
POPULAR_ASX_STOCKS = [
    "CBA",  # Commonwealth Bank
    "BHP",  # BHP Group
    "CSL",  # CSL Limited
    "NAB",  # National Australia Bank
    "WBC",  # Westpac
    "ANZ",  # ANZ Bank
    "WES",  # Wesfarmers
    "MQG",  # Macquarie Group
    "WOW",  # Woolworths
    "TLS",  # Telstra
    "RIO",  # Rio Tinto
    "FMG",  # Fortescue Metals
    "GMG",  # Goodman Group
    "WDS",  # Woodside Energy
    "TCL",  # Transurban Group
]
