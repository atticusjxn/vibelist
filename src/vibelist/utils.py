"""
Utility functions for VibeList
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)


def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry a function with exponential backoff

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry on

    Returns:
        Function result if successful
    """
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries:
                logger.error(f"Function failed after {max_retries} retries: {str(e)}")
                raise

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.1f}s...")
            time.sleep(delay)


def validate_trading_hours() -> bool:
    """
    Check if current time is during market hours

    Returns:
        True if during market hours, False otherwise
    """
    now = datetime.now()

    # Check if it's a weekday
    if now.weekday() >= 5:  # Saturday (5) or Sunday (6)
        return False

    # Check if it's during market hours (9:30 AM - 4:00 PM ET)
    # This is a simplified check - you may want to enhance with timezone handling
    hour = now.hour
    minute = now.minute
    current_time = hour + minute / 60.0

    # Market hours: 9:30 AM to 4:00 PM ET
    market_open = 9.5  # 9:30 AM
    market_close = 16.0  # 4:00 PM

    return market_open <= current_time <= market_close


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency amount

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_percentage(value: float, include_sign: bool = True) -> str:
    """
    Format percentage value

    Args:
        value: Percentage value (e.g., 0.154 for 15.4%)
        include_sign: Whether to include + sign for positive values

    Returns:
        Formatted percentage string
    """
    percentage = value * 100
    if include_sign and percentage > 0:
        return f"+{percentage:.2f}%"
    else:
        return f"{percentage:.2f}%"


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value
    """
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length

    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_time_periods_for_analysis() -> Dict[str, int]:
    """
    Get time periods for sentiment analysis

    Returns:
        Dictionary with period names and hour values
    """
    return {
        "last_24_hours": 24,
        "last_12_hours": 12,
        "last_6_hours": 6,
        "last_hour": 1
    }


def calculate_portfolio_value_change(
    current_values: Dict[str, float],
    previous_values: Dict[str, float],
    weights: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate portfolio value change

    Args:
        current_values: Current stock prices
        previous_values: Previous stock prices
        weights: Portfolio weights

    Returns:
        Dictionary with change metrics
    """
    total_change = 0.0
    total_value = 0.0
    total_weighted_change = 0.0

    for symbol, current_price in current_values.items():
        if symbol in previous_values and symbol in weights:
            weight = weights[symbol]
            previous_price = previous_values[symbol]

            if previous_price > 0:
                change_pct = (current_price - previous_price) / previous_price
                weighted_change = change_pct * weight
                total_weighted_change += weighted_change

    return {
        "portfolio_change_percent": total_weighted_change * 100,
        "is_positive": total_weighted_change > 0
    }


def validate_email_address(email: str) -> bool:
    """
    Basic email address validation

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_stock_market_holidays(year: int) -> List[datetime]:
    """
    Get US stock market holidays for a given year

    Args:
        year: Year to get holidays for

    Returns:
        List of holiday dates
    """
    # This is a simplified list - you may want to enhance this
    holidays = []

    # New Year's Day
    holidays.append(datetime(year, 1, 1))

    # Martin Luther King Jr. Day (3rd Monday in January)
    import calendar
    mlk_day = datetime(year, 1, 1)
    while mlk_day.weekday() != 0 or mlk_day.day < 15:
        mlk_day += timedelta(days=1)
    holidays.append(mlk_day)

    # Presidents Day (3rd Monday in February)
    presidents_day = datetime(year, 2, 1)
    while presidents_day.weekday() != 0 or presidents_day.day < 15:
        presidents_day += timedelta(days=1)
    holidays.append(presidents_day)

    # Add more holidays as needed...

    return holidays


def is_market_closed_today() -> bool:
    """
    Check if market is closed today (weekend or holiday)

    Returns:
        True if market is closed, False otherwise
    """
    today = datetime.now()

    # Check weekend
    if today.weekday() >= 5:
        return True

    # Check holidays
    holidays = get_stock_market_holidays(today.year)
    for holiday in holidays:
        if holiday.date() == today.date():
            return True

    return False