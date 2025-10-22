"""
Configuration management for VibeList
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class StockConfig(BaseModel):
    """Configuration for a single stock in the portfolio"""
    symbol: str = Field(..., description="Stock ticker symbol")
    weight: float = Field(..., ge=0, le=1, description="Portfolio weight (0-1)")

    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()

    @validator('weight')
    def validate_weight(cls, v):
        if v <= 0 or v > 1:
            raise ValueError("Weight must be between 0 and 1")
        return v


class PortfolioConfig(BaseModel):
    """Configuration for the entire portfolio"""
    stocks: List[StockConfig] = Field(..., description="List of stocks in portfolio")
    email: str = Field(..., description="Email address to send digest to")

    @validator('stocks')
    def validate_stocks(cls, v):
        if not v:
            raise ValueError("Portfolio must contain at least one stock")

        # Check that weights sum to 1.0 (with small tolerance)
        total_weight = sum(stock.weight for stock in v)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Portfolio weights must sum to 1.0, got {total_weight:.3f}")

        # Check for duplicate symbols
        symbols = [stock.symbol for stock in v]
        if len(symbols) != len(set(symbols)):
            raise ValueError("Portfolio contains duplicate stock symbols")

        return v


class APIConfig(BaseModel):
    """API configuration"""
    xai_api_key: str = Field(..., description="xAI API key")
    xai_model: str = Field(default="grok-4-fast", description="xAI model identifier")
    xai_base_url: str = Field(default="https://api.x.ai/v1", description="xAI API base URL")
    resend_api_key: str = Field(..., description="Resend API key")
    from_email: str = Field(..., description="From email address")


class VibeListConfig(BaseModel):
    """Main configuration for VibeList"""
    portfolio: PortfolioConfig
    api: APIConfig
    log_level: str = Field(default="INFO", description="Logging level")
    portfolio_config_path: str = Field(default="config/portfolio.json", description="Path to portfolio config file")


def load_config(portfolio_path: Optional[str] = None) -> VibeListConfig:
    """Load configuration from environment and portfolio file"""

    # Load portfolio configuration
    if portfolio_path is None:
        portfolio_path = os.getenv("PORTFOLIO_CONFIG_PATH", "config/portfolio.json")

    portfolio_file = Path(portfolio_path)
    if not portfolio_file.exists():
        raise FileNotFoundError(f"Portfolio configuration file not found: {portfolio_path}")

    with open(portfolio_file, 'r') as f:
        portfolio_data = json.load(f)

    # Create portfolio config
    portfolio_config = PortfolioConfig(**portfolio_data)

    # Create API config
    api_config = APIConfig(
        xai_api_key=os.getenv("XAI_API_KEY", ""),
        xai_model=os.getenv("XAI_MODEL", "grok-4-fast"),
        xai_base_url=os.getenv("XAI_API_BASE_URL", "https://api.x.ai/v1"),
        resend_api_key=os.getenv("RESEND_API_KEY", ""),
        from_email=os.getenv("FROM_EMAIL", "")
    )

    # Validate API keys
    if not api_config.xai_api_key:
        raise ValueError("XAI_API_KEY environment variable is required")
    if not api_config.resend_api_key:
        raise ValueError("RESEND_API_KEY environment variable is required")
    if not api_config.from_email:
        raise ValueError("FROM_EMAIL environment variable is required")

    # Create main config
    config = VibeListConfig(
        portfolio=portfolio_config,
        api=api_config,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        portfolio_config_path=portfolio_path
    )

    return config


def create_sample_portfolio(output_path: str = "config/portfolio.json"):
    """Create a sample portfolio configuration file"""

    sample_portfolio = {
        "stocks": [
            {"symbol": "NVDA", "weight": 0.321},  # 32.1% - $1,842.20
            {"symbol": "PLTR", "weight": 0.210},  # 21.0% - $1,206.40
            {"symbol": "SMCI", "weight": 0.126},  # 12.6% - $724.80
            {"symbol": "SNAP", "weight": 0.088},  # 8.8% - $506.40
            {"symbol": "RIVN", "weight": 0.088},  # 8.8% - $506.40
            {"symbol": "AAPL", "weight": 0.059},  # 5.9% - $339.20
            {"symbol": "GOOGL", "weight": 0.045},  # 4.5% - $258.40
            {"symbol": "MSFT", "weight": 0.023},  # 2.3% - $132.00
            {"symbol": "AMD", "weight": 0.014},  # 1.4% - $80.40
            {"symbol": "TSLA", "weight": 0.014},  # 1.4% - $80.40
            {"symbol": "AMZN", "weight": 0.007},  # 0.7% - $40.20
            {"symbol": "COIN", "weight": 0.005}   # 0.5% - $28.60
        ],
        "email": "your-email@example.com"
    }

    # Create config directory if it doesn't exist
    config_dir = Path(output_path).parent
    config_dir.mkdir(exist_ok=True)

    # Write sample portfolio
    with open(output_path, 'w') as f:
        json.dump(sample_portfolio, f, indent=2)

    print(f"Sample portfolio created at: {output_path}")
    print("Please update the email address and stock weights before running.")
