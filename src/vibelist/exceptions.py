"""
Custom exceptions for VibeList
"""


class VibeListError(Exception):
    """Base exception for VibeList"""
    pass


class ConfigurationError(VibeListError):
    """Raised when there's an issue with configuration"""
    pass


class APIError(VibeListError):
    """Raised when there's an issue with external APIs"""
    pass


class StockDataError(VibeListError):
    """Raised when there's an issue fetching stock data"""
    pass


class SentimentAnalysisError(VibeListError):
    """Raised when there's an issue with sentiment analysis"""
    pass


class EmailError(VibeListError):
    """Raised when there's an issue sending emails"""
    pass


class PortfolioAnalysisError(VibeListError):
    """Raised when there's an issue with portfolio analysis"""
    pass