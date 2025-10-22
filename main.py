#!/usr/bin/env python3
"""
VibeList - Daily Stock Portfolio Digest

Main script for generating and sending daily portfolio digests with X sentiment analysis.
"""

import sys
import argparse
import json
import logging
import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vibelist.config import load_config
from vibelist.stock_data import StockDataFetcher
from vibelist.sentiment import GrokAPIClient
from vibelist.analyzer import RecommendationEngine
from vibelist.email_generator import EmailGenerator
from vibelist.email_sender import EmailSender


PERSONAL_PORTFOLIO_HOLDINGS: List[Dict[str, Any]] = [
    {
        "symbol": "AVUV",
        "name": "Avantis U.S. Small Cap Value ETF",
        "shares": 0.563,
        "market_value": 55.62,
        "price": 98.78,
        "day_change": 0.23,
        "day_change_pct": 0.23,
        "after_hours": 0.26,
        "after_hours_pct": 0.26,
        "daily_pl": 0.13,
        "return_dollars": 2.28,
        "return_percent": 4.27,
    },
    {
        "symbol": "HOOD",
        "name": "Robinhood Markets, Inc.",
        "shares": 0.6003,
        "market_value": 79.15,
        "price": 131.84,
        "day_change": -3.96,
        "day_change_pct": -2.92,
        "after_hours": -1.74,
        "after_hours_pct": -1.32,
        "daily_pl": -2.38,
        "return_dollars": -3.11,
        "return_percent": -3.78,
    },
    {
        "symbol": "PATH",
        "name": "UiPath, Inc.",
        "shares": 9.0604,
        "market_value": 147.50,
        "price": 16.28,
        "day_change": 0.35,
        "day_change_pct": 2.20,
        "after_hours": 0.02,
        "after_hours_pct": 0.12,
        "daily_pl": 3.17,
        "return_dollars": 4.25,
        "return_percent": 2.97,
    },
    {
        "symbol": "QQQM",
        "name": "INVESCO NASDAQ 100 ETF",
        "shares": 1.2569,
        "market_value": 316.35,
        "price": 251.69,
        "day_change": -0.07,
        "day_change_pct": -0.03,
        "after_hours": -0.41,
        "after_hours_pct": -0.16,
        "daily_pl": -0.09,
        "return_dollars": 71.36,
        "return_percent": 29.13,
    },
    {
        "symbol": "SLNH",
        "name": "Soluna Holdings Inc",
        "shares": 11.0821,
        "market_value": 38.57,
        "price": 3.48,
        "day_change": -0.47,
        "day_change_pct": -11.90,
        "after_hours": -0.13,
        "after_hours_pct": -3.74,
        "daily_pl": -5.21,
        "return_dollars": -7.74,
        "return_percent": -16.72,
    },
    {
        "symbol": "SMH",
        "name": "VanEck Vectors Semiconductor ETF",
        "shares": 0.4749,
        "market_value": 163.99,
        "price": 345.30,
        "day_change": -1.92,
        "day_change_pct": -0.55,
        "after_hours": -1.80,
        "after_hours_pct": -0.52,
        "daily_pl": -0.91,
        "return_dollars": 49.69,
        "return_percent": 43.47,
    },
    {
        "symbol": "SOUN",
        "name": "SOUNDHOUND AI INC",
        "shares": 4.5236,
        "market_value": 82.46,
        "price": 18.23,
        "day_change": -0.83,
        "day_change_pct": -4.35,
        "after_hours": -0.15,
        "after_hours_pct": -0.82,
        "daily_pl": -3.75,
        "return_dollars": -4.63,
        "return_percent": -5.31,
    },
    {
        "symbol": "TSM",
        "name": "Taiwan Semiconductor Manufacturing Co.",
        "shares": 0.2507,
        "market_value": 73.82,
        "price": 294.51,
        "day_change": -3.19,
        "day_change_pct": -1.07,
        "after_hours": -0.35,
        "after_hours_pct": -0.12,
        "daily_pl": -0.80,
        "return_dollars": -1.13,
        "return_percent": -1.50,
    },
    {
        "symbol": "VOO",
        "name": "S&P 500 Vanguard ETF",
        "shares": 0.051,
        "market_value": 31.46,
        "price": 617.09,
        "day_change": -0.08,
        "day_change_pct": -0.01,
        "after_hours": -0.15,
        "after_hours_pct": -0.02,
        "daily_pl": 0.00,
        "return_dollars": 5.46,
        "return_percent": 20.99,
    },
]


def _calculate_weighted_holdings(
    holdings: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Decimal]:
    """Convert raw holdings into rounded portfolio weights."""
    total_value = sum(Decimal(str(item["market_value"])) for item in holdings)
    if total_value == 0:
        raise ValueError("Total market value cannot be zero")

    weighted_entries: List[Dict[str, Any]] = []
    for holding in holdings:
        market_value = Decimal(str(holding["market_value"]))
        raw_weight = market_value / total_value
        rounded_weight = raw_weight.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        weighted_entries.append(
            {
                "holding": holding,
                "market_value": market_value,
                "raw_weight": raw_weight,
                "rounded_weight": rounded_weight,
            }
        )

    # Adjust rounding so weights sum exactly to 1.0000
    rounded_total = sum(entry["rounded_weight"] for entry in weighted_entries)
    diff = Decimal("1.0000") - rounded_total
    if diff != Decimal("0"):
        adjust_entry = max(weighted_entries, key=lambda entry: entry["raw_weight"])
        adjust_entry["rounded_weight"] = (adjust_entry["rounded_weight"] + diff).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

    return weighted_entries, total_value


def create_personal_portfolio_config(
    output_path: Optional[str] = None,
    email: Optional[str] = None,
) -> Path:
    """
    Create a portfolio config file using holdings from PERSONAL_PORTFOLIO_HOLDINGS.

    Args:
        output_path: Optional path to write config (defaults to env or config/portfolio.json)
        email: Optional override for destination email address

    Returns:
        Path to the written configuration file
    """
    logger = logging.getLogger(__name__)
    logger.info("Building portfolio configuration from personal holdings snapshot")

    weighted_entries, total_value = _calculate_weighted_holdings(PERSONAL_PORTFOLIO_HOLDINGS)

    portfolio_email = (
        email
        or os.getenv("TO_EMAIL")
        or os.getenv("PORTFOLIO_EMAIL")
        or "your-email@example.com"
    )

    stocks = [
        {"symbol": entry["holding"]["symbol"], "weight": float(entry["rounded_weight"])}
        for entry in weighted_entries
    ]
    portfolio_config = {"stocks": stocks, "email": portfolio_email}

    if output_path is None:
        output_path = os.getenv("PORTFOLIO_CONFIG_PATH", "config/portfolio.json")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(portfolio_config, f, indent=2)

    logger.info(
        "Personal portfolio config saved to %s (total market value $%.2f)",
        output_file,
        float(total_value),
    )

    for entry in weighted_entries:
        holding = entry["holding"]
        percent = (entry["rounded_weight"] * Decimal("100")).quantize(Decimal("0.01"))
        logger.info(
            "  %s: %s shares at $%.2f -> $%.2f (%s%% weight)",
            holding["symbol"],
            holding["shares"],
            holding["price"],
            holding["market_value"],
            percent,
        )

    return output_file


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Configure logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/vibelist_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set colorlog for console output if available
    try:
        import colorlog
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))
        logging.getLogger().handlers[1] = handler
    except ImportError:
        pass  # Use default formatting if colorlog not available

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level: {log_level}")


def generate_daily_digest(config_path: Optional[str] = None, test_mode: bool = False) -> bool:
    """
    Generate and send daily portfolio digest

    Args:
        config_path: Path to portfolio configuration file
        test_mode: If True, run in test mode without sending emails

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting VibeList daily digest generation")

        # Load configuration
        logger.info("Loading configuration...")
        try:
            config = load_config(config_path)
        except FileNotFoundError:
            logger.warning(
                "Portfolio configuration not found. Creating one from personal holdings snapshot."
            )
            created_path = create_personal_portfolio_config(config_path)
            config = load_config(str(created_path))
        logger.info(f"Configuration loaded for {len(config.portfolio.stocks)} stocks")

        # Initialize components
        stock_fetcher = StockDataFetcher()
        grok_client = GrokAPIClient(config.api.grok_api_key)
        recommendation_engine = RecommendationEngine()
        email_generator = EmailGenerator()
        email_sender = EmailSender(config.api.resend_api_key, config.api.from_email)

        # Validate email configuration
        if not email_sender.validate_configuration():
            raise ValueError("Email configuration validation failed")

        # Extract stock symbols
        stock_symbols = [stock.symbol for stock in config.portfolio.stocks]

        # Fetch stock data
        logger.info("Fetching stock market data...")
        stock_data = stock_fetcher.get_multiple_stocks(stock_symbols)

        if not stock_data:
            raise ValueError("No stock data could be fetched")

        logger.info(f"Successfully fetched data for {len(stock_data)} stocks")

        # Analyze sentiment
        logger.info("Analyzing X sentiment...")
        sentiment_data = grok_client.batch_analyze(stock_symbols)

        if not sentiment_data:
            raise ValueError("No sentiment data could be analyzed")

        logger.info(f"Successfully analyzed sentiment for {len(sentiment_data)} stocks")

        # Generate recommendations and analysis
        logger.info("Generating recommendations...")
        stock_analyses = {}

        for stock_config in config.portfolio.stocks:
            symbol = stock_config.symbol

            if symbol in stock_data and symbol in sentiment_data:
                analysis = recommendation_engine.analyze_stock(
                    stock_data[symbol],
                    sentiment_data[symbol],
                    stock_config.weight
                )
                stock_analyses[symbol] = analysis
            else:
                logger.warning(f"Missing data for {symbol}, skipping")

        if not stock_analyses:
            raise ValueError("No complete analyses could be generated")

        # Analyze overall portfolio
        logger.info("Analyzing portfolio performance...")
        portfolio_analysis = recommendation_engine.analyze_portfolio(stock_analyses)

        # Generate email content
        logger.info("Generating email content...")
        html_content = email_generator.generate_email_html(portfolio_analysis)
        text_content = email_generator.generate_text_summary(portfolio_analysis)

        # Send email (unless in test mode)
        if not test_mode:
            logger.info("Sending daily digest email...")
            subject = email_sender.create_digest_subject(
                portfolio_analysis.portfolio_score,
                portfolio_analysis.last_updated
            )

            response = email_sender.send_daily_digest(
                to_email=config.portfolio.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            logger.info(f"Email sent successfully! Response: {response}")
        else:
            logger.info("TEST MODE: Skipping email delivery")
            # Save email content to file for testing
            test_file = f"logs/test_digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(test_file, 'w') as f:
                f.write(html_content)
            logger.info(f"Test email saved to: {test_file}")

        # Log summary
        logger.info("Daily digest generation completed successfully!")
        logger.info(f"Portfolio Score: {portfolio_analysis.portfolio_score:+.3f}")
        logger.info(f"Stocks Analyzed: {len(stock_analyses)}")
        logger.info(f"Recommendations: {sum(1 for a in stock_analyses.values() if a.recommendation == 'BUY')} BUY, "
                   f"{sum(1 for a in stock_analyses.values() if a.recommendation == 'HOLD')} HOLD, "
                   f"{sum(1 for a in stock_analyses.values() if a.recommendation == 'SELL')} SELL")

        return True

    except Exception as e:
        logger.error(f"Error generating daily digest: {str(e)}")
        return False


def test_configuration(config_path: Optional[str] = None):
    """Test configuration and send test email"""
    logger = logging.getLogger(__name__)

    try:
        logger.info("Testing VibeList configuration...")

        # Load configuration
        try:
            config = load_config(config_path)
        except FileNotFoundError:
            logger.warning(
                "Portfolio configuration not found. Creating one from personal holdings snapshot."
            )
            created_path = create_personal_portfolio_config(config_path)
            config = load_config(str(created_path))
        logger.info("✓ Configuration loaded successfully")

        # Test email configuration
        email_sender = EmailSender(config.api.resend_api_key, config.api.from_email)
        if email_sender.validate_configuration():
            logger.info("✓ Email configuration is valid")

            # Send test email
            logger.info("Sending test email...")
            response = email_sender.send_test_email(config.portfolio.email)
            logger.info(f"✓ Test email sent successfully! ID: {response['id']}")
        else:
            logger.error("✗ Email configuration is invalid")
            return False

        # Test stock data fetching
        stock_fetcher = StockDataFetcher()
        test_symbol = config.portfolio.stocks[0].symbol
        logger.info(f"Testing stock data fetch with {test_symbol}...")
        stock_info = stock_fetcher.get_stock_info(test_symbol)
        logger.info(f"✓ Stock data fetched successfully: {test_symbol} @ ${stock_info.current_price}")

        logger.info("All configuration tests passed!")
        return True

    except Exception as e:
        logger.error(f"Configuration test failed: {str(e)}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="VibeList Daily Portfolio Digest")
    parser.add_argument("--config", "-c", help="Path to portfolio configuration file")
    parser.add_argument("--test", "-t", action="store_true", help="Test configuration and send test email")
    parser.add_argument("--dry-run", "-d", action="store_true", help="Generate digest without sending email")
    parser.add_argument("--create-sample", action="store_true", help="Create sample portfolio configuration")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Handle different commands
    if args.create_sample:
        created_path = create_personal_portfolio_config(args.config)
        logging.getLogger(__name__).info(
            "Personalized portfolio configuration created at %s", created_path
        )
        return 0

    if args.test:
        success = test_configuration(args.config)
        return 0 if success else 1

    # Generate daily digest
    success = generate_daily_digest(args.config, test_mode=args.dry_run)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
