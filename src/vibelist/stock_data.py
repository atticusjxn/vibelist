"""
Stock data fetching using Yahoo Finance API
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class StockInfo(BaseModel):
    """Model for stock information"""
    symbol: str
    current_price: float
    previous_close: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[int] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    last_updated: datetime
    currency: str = "USD"


class StockDataFetcher:
    """Handles fetching stock data from Yahoo Finance"""

    def __init__(self):
        self.session = None

    def get_stock_info(self, symbol: str) -> StockInfo:
        """
        Fetch comprehensive stock information for a given symbol

        Args:
            symbol: Stock ticker symbol

        Returns:
            StockInfo object with current stock data

        Raises:
            ValueError: If symbol is invalid or data cannot be fetched
        """
        try:
            symbol = symbol.upper().strip()
            logger.info(f"Fetching stock data for {symbol}")

            # Create ticker object
            ticker = yf.Ticker(symbol)

            # Get historical data for recent prices
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            # Fetch data
            hist_data = ticker.history(start=start_date, end=end_date, interval="1d")

            if hist_data.empty:
                raise ValueError(f"No historical data found for {symbol}")

            # Get current/recent price
            latest_data = hist_data.iloc[-1]
            previous_data = hist_data.iloc[-2] if len(hist_data) > 1 else latest_data

            current_price = latest_data['Close']
            previous_close = previous_data['Close']
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close > 0 else 0

            # Get additional info
            info = ticker.info

            # Create StockInfo object
            stock_info = StockInfo(
                symbol=symbol,
                current_price=round(current_price, 2),
                previous_close=round(previous_close, 2),
                change=round(change, 2),
                change_percent=round(change_percent, 2),
                volume=int(latest_data['Volume']),
                market_cap=info.get('marketCap'),
                day_high=round(latest_data['High'], 2) if pd.notna(latest_data['High']) else None,
                day_low=round(latest_data['Low'], 2) if pd.notna(latest_data['Low']) else None,
                week_52_high=info.get('fiftyTwoWeekHigh'),
                week_52_low=info.get('fiftyTwoWeekLow'),
                last_updated=datetime.now(),
                currency=info.get('currency', 'USD')
            )

            logger.info(f"Successfully fetched data for {symbol}: ${stock_info.current_price} ({stock_info.change_percent:+.2f}%)")
            return stock_info

        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            raise ValueError(f"Failed to fetch data for {symbol}: {str(e)}")

    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, StockInfo]:
        """
        Fetch stock information for multiple symbols

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dictionary mapping symbols to StockInfo objects
        """
        results = {}
        errors = []

        for symbol in symbols:
            try:
                stock_info = self.get_stock_info(symbol)
                results[symbol] = stock_info
            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")
                logger.warning(f"Failed to fetch data for {symbol}: {str(e)}")

        if errors:
            logger.warning(f"Failed to fetch data for some stocks: {'; '.join(errors)}")

        return results

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a stock symbol exists and is tradeable

        Args:
            symbol: Stock ticker symbol to validate

        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            symbol = symbol.upper().strip()
            ticker = yf.Ticker(symbol)

            # Try to get basic info
            info = ticker.info

            # Check if we got valid data
            return (
                info is not None and
                'regularMarketPrice' in info or
                'currentPrice' in info or
                'symbol' in info
            )

        except Exception as e:
            logger.debug(f"Symbol validation failed for {symbol}: {str(e)}")
            return False

    def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status information

        Returns:
            Dictionary with market status information
        """
        try:
            # Get market status using SPY as a reference
            spy = yf.Ticker("SPY")
            hist = spy.history(period="1d", interval="1m")

            if hist.empty:
                return {"status": "closed", "message": "No market data available"}

            last_time = hist.index[-1]
            current_time = datetime.now()

            # Simple market hours check (9:30 AM - 4:00 PM ET, Mon-Fri)
            # This is a simplified check - you may want to enhance this
            is_weekday = current_time.weekday() < 5

            market_hours = {
                "status": "open" if is_weekday else "closed",
                "last_update": last_time,
                "current_time": current_time,
                "is_weekday": is_weekday
            }

            return market_hours

        except Exception as e:
            logger.error(f"Error getting market status: {str(e)}")
            return {"status": "unknown", "message": str(e)}