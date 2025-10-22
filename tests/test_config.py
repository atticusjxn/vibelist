"""
Tests for VibeList configuration
"""

import pytest
import tempfile
import json
import os
from pathlib import Path

from vibelist.config import (
    StockConfig, PortfolioConfig, APIConfig, VibeListConfig,
    load_config, create_sample_portfolio
)


class TestStockConfig:
    """Test StockConfig model"""

    def test_valid_stock_config(self):
        config = StockConfig(symbol="AAPL", weight=0.5)
        assert config.symbol == "AAPL"
        assert config.weight == 0.5

    def test_symbol_normalization(self):
        config = StockConfig(symbol="aapl", weight=0.5)
        assert config.symbol == "AAPL"

    def test_weight_validation(self):
        with pytest.raises(ValueError):
            StockConfig(symbol="AAPL", weight=1.5)

        with pytest.raises(ValueError):
            StockConfig(symbol="AAPL", weight=-0.1)

        with pytest.raises(ValueError):
            StockConfig(symbol="AAPL", weight=0)


class TestPortfolioConfig:
    """Test PortfolioConfig model"""

    def test_valid_portfolio_config(self):
        stocks = [
            StockConfig(symbol="AAPL", weight=0.4),
            StockConfig(symbol="TSLA", weight=0.3),
            StockConfig(symbol="NVDA", weight=0.3)
        ]
        config = PortfolioConfig(stocks=stocks, email="test@example.com")
        assert len(config.stocks) == 3
        assert config.email == "test@example.com"

    def test_weight_sum_validation(self):
        stocks = [
            StockConfig(symbol="AAPL", weight=0.4),
            StockConfig(symbol="TSLA", weight=0.3),
            StockConfig(symbol="NVDA", weight=0.2)  # Total 0.9, not 1.0
        ]
        with pytest.raises(ValueError):
            PortfolioConfig(stocks=stocks, email="test@example.com")

    def test_duplicate_symbols(self):
        stocks = [
            StockConfig(symbol="AAPL", weight=0.4),
            StockConfig(symbol="AAPL", weight=0.6)  # Duplicate
        ]
        with pytest.raises(ValueError):
            PortfolioConfig(stocks=stocks, email="test@example.com")

    def test_empty_portfolio(self):
        with pytest.raises(ValueError):
            PortfolioConfig(stocks=[], email="test@example.com")


class TestAPIConfig:
    """Test APIConfig model"""

    def test_valid_api_config(self):
        config = APIConfig(
            xai_api_key="test_key",
            resend_api_key="test_key",
            from_email="test@example.com"
        )
        assert config.xai_api_key == "test_key"
        assert config.resend_api_key == "test_key"
        assert config.from_email == "test@example.com"


def test_create_sample_portfolio():
    """Test creating sample portfolio"""
    with tempfile.TemporaryDirectory() as temp_dir:
        sample_path = os.path.join(temp_dir, "sample_portfolio.json")
        create_sample_portfolio(sample_path)

        assert os.path.exists(sample_path)

        with open(sample_path, 'r') as f:
            data = json.load(f)

        assert "stocks" in data
        assert "email" in data
        assert len(data["stocks"]) == 3
        assert data["email"] == "your-email@example.com"


def test_load_config_missing_file():
    """Test loading config with missing file"""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_file.json")


def test_load_config_missing_env_vars():
    """Test loading config with missing environment variables"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "portfolio.json")

        portfolio_data = {
            "stocks": [{"symbol": "AAPL", "weight": 1.0}],
            "email": "test@example.com"
        }

        with open(config_path, 'w') as f:
            json.dump(portfolio_data, f)

        # Clear environment variables
        old_xai = os.environ.pop("XAI_API_KEY", None)
        old_resend = os.environ.pop("RESEND_API_KEY", None)
        old_from = os.environ.pop("FROM_EMAIL", None)

        try:
            with pytest.raises(ValueError, match="XAI_API_KEY"):
                load_config(config_path)
        finally:
            # Restore environment variables
            if old_xai:
                os.environ["XAI_API_KEY"] = old_xai
            if old_resend:
                os.environ["RESEND_API_KEY"] = old_resend
            if old_from:
                os.environ["FROM_EMAIL"] = old_from
