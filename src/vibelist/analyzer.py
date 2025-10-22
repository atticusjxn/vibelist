"""
Stock analysis and recommendation engine
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
import logging

from .stock_data import StockInfo
from .sentiment import SentimentScore

logger = logging.getLogger(__name__)


class StockAnalysis(BaseModel):
    """Complete analysis for a single stock"""
    symbol: str
    stock_info: StockInfo
    sentiment_score: SentimentScore
    recommendation: str  # "BUY", "SELL", "HOLD"
    reasoning: str
    portfolio_weight: float
    score: float  # Overall investment score (-1.0 to 1.0)
    last_updated: datetime


class PortfolioAnalysis(BaseModel):
    """Complete analysis for the entire portfolio"""
    overall_sentiment: float
    portfolio_score: float
    top_performers: List[str]
    underperformers: List[str]
    key_insights: List[str]
    market_summary: str
    stock_analyses: Dict[str, StockAnalysis]
    last_updated: datetime


class RecommendationEngine:
    """Engine for generating stock recommendations based on data and sentiment"""

    def __init__(self):
        self.sentiment_weight = 0.4  # Weight for sentiment in overall score
        self.price_weight = 0.6      # Weight for price performance in overall score

    def analyze_stock(
        self,
        stock_info: StockInfo,
        sentiment_score: SentimentScore,
        portfolio_weight: float
    ) -> StockAnalysis:
        """
        Perform complete analysis of a single stock

        Args:
            stock_info: Current stock data
            sentiment_score: Sentiment analysis results
            portfolio_weight: Weight in portfolio (0-1)

        Returns:
            StockAnalysis with complete analysis and recommendation
        """
        try:
            logger.info(f"Analyzing {stock_info.symbol} for recommendation")

            # Calculate price performance score
            price_score = self._calculate_price_score(stock_info)

            # Normalize sentiment score (-1 to 1)
            sentiment_score_normalized = sentiment_score.overall_sentiment

            # Calculate overall score
            overall_score = (
                price_score * self.price_weight +
                sentiment_score_normalized * self.sentiment_weight
            )

            # Generate recommendation
            recommendation = self._generate_recommendation(overall_score, sentiment_score, stock_info)

            # Generate reasoning
            reasoning = self._generate_reasoning(
                stock_info, sentiment_score, overall_score, recommendation
            )

            analysis = StockAnalysis(
                symbol=stock_info.symbol,
                stock_info=stock_info,
                sentiment_score=sentiment_score,
                recommendation=recommendation,
                reasoning=reasoning,
                portfolio_weight=portfolio_weight,
                score=round(overall_score, 3),
                last_updated=datetime.now()
            )

            logger.info(f"Analysis complete for {stock_info.symbol}: {recommendation} (Score: {overall_score:+.3f})")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing {stock_info.symbol}: {str(e)}")
            raise

    def analyze_portfolio(self, stock_analyses: Dict[str, StockAnalysis]) -> PortfolioAnalysis:
        """
        Analyze the entire portfolio and generate insights

        Args:
            stock_analyses: Dictionary of stock analyses

        Returns:
            PortfolioAnalysis with complete portfolio insights
        """
        try:
            logger.info("Analyzing portfolio performance")

            if not stock_analyses:
                raise ValueError("No stock analyses provided")

            # Calculate portfolio-wide metrics
            overall_sentiment = sum(
                analysis.sentiment_score.overall_sentiment * analysis.portfolio_weight
                for analysis in stock_analyses.values()
            )

            portfolio_score = sum(
                analysis.score * analysis.portfolio_weight
                for analysis in stock_analyses.values()
            )

            # Identify top and underperformers
            sorted_by_score = sorted(
                stock_analyses.items(),
                key=lambda x: x[1].score,
                reverse=True
            )

            top_performers = [symbol for symbol, _ in sorted_by_score[:2]]
            underperformers = [symbol for symbol, _ in sorted_by_score[-2:]]

            # Generate key insights
            key_insights = self._generate_portfolio_insights(stock_analyses)

            # Generate market summary
            market_summary = self._generate_market_summary(stock_analyses)

            portfolio_analysis = PortfolioAnalysis(
                overall_sentiment=round(overall_sentiment, 3),
                portfolio_score=round(portfolio_score, 3),
                top_performers=top_performers,
                underperformers=underperformers,
                key_insights=key_insights,
                market_summary=market_summary,
                stock_analyses=stock_analyses,
                last_updated=datetime.now()
            )

            logger.info(f"Portfolio analysis complete: Score {portfolio_score:+.3f}")
            return portfolio_analysis

        except Exception as e:
            logger.error(f"Error analyzing portfolio: {str(e)}")
            raise

    def _calculate_price_score(self, stock_info: StockInfo) -> float:
        """
        Calculate price performance score

        Args:
            stock_info: Stock information

        Returns:
            Price score (-1.0 to 1.0)
        """
        # Use daily change as primary factor
        change_score = stock_info.change_percent / 100.0

        # Cap extreme values
        change_score = max(-1.0, min(1.0, change_score))

        # Consider volume (higher volume = more significant moves)
        volume_factor = min(1.0, stock_info.volume / 1_000_000)  # Normalize to millions

        # Combine factors
        price_score = change_score * (0.7 + 0.3 * volume_factor)

        return price_score

    def _generate_recommendation(
        self,
        overall_score: float,
        sentiment_score: SentimentScore,
        stock_info: StockInfo
    ) -> str:
        """
        Generate buy/sell/hold recommendation

        Args:
            overall_score: Combined analysis score
            sentiment_score: Sentiment analysis
            stock_info: Stock information

        Returns:
            Recommendation string
        """
        # Strong buy criteria
        if overall_score > 0.5 and sentiment_score.confidence > 0.6:
            return "BUY"

        # Strong sell criteria
        if overall_score < -0.5 and sentiment_score.confidence > 0.6:
            return "SELL"

        # Moderate buy
        if overall_score > 0.2:
            return "BUY"

        # Moderate sell
        if overall_score < -0.2:
            return "SELL"

        # Default to hold
        return "HOLD"

    def _generate_reasoning(
        self,
        stock_info: StockInfo,
        sentiment_score: SentimentScore,
        overall_score: float,
        recommendation: str
    ) -> str:
        """
        Generate reasoning for the recommendation

        Args:
            stock_info: Stock information
            sentiment_score: Sentiment analysis
            overall_score: Overall analysis score
            recommendation: Generated recommendation

        Returns:
            Reasoning string
        """
        reasons = []

        # Price performance reasoning
        if stock_info.change_percent > 2:
            reasons.append(f"Strong price performance (+{stock_info.change_percent:.1f}%)")
        elif stock_info.change_percent < -2:
            reasons.append(f"Poor price performance ({stock_info.change_percent:.1f}%)")
        else:
            reasons.append(f"Modest price movement ({stock_info.change_percent:+.1f}%)")

        # Sentiment reasoning
        if sentiment_score.confidence > 0.6:
            if sentiment_score.overall_sentiment > 0.3:
                reasons.append(f"Positive X sentiment ({sentiment_score.overall_sentiment:+.2f})")
            elif sentiment_score.overall_sentiment < -0.3:
                reasons.append(f"Negative X sentiment ({sentiment_score.overall_sentiment:+.2f})")
            else:
                reasons.append("Neutral X sentiment")
        else:
            reasons.append("Low confidence sentiment data")

        # Volume reasoning
        if stock_info.volume > 5_000_000:  # High volume threshold
            reasons.append("High trading volume supports price move")

        # Combine into recommendation reasoning
        base_reasoning = "; ".join(reasons)

        if recommendation == "BUY":
            return f"{base_reasoning}. Positive indicators suggest potential upside."
        elif recommendation == "SELL":
            return f"{base_reasoning}. Negative indicators suggest caution."
        else:
            return f"{base_reasoning}. Mixed signals warrant holding position."

    def _generate_portfolio_insights(self, stock_analyses: Dict[str, StockAnalysis]) -> List[str]:
        """Generate key insights about the portfolio"""
        insights = []

        # Overall portfolio health
        buy_count = sum(1 for a in stock_analyses.values() if a.recommendation == "BUY")
        sell_count = sum(1 for a in stock_analyses.values() if a.recommendation == "SELL")
        hold_count = sum(1 for a in stock_analyses.values() if a.recommendation == "HOLD")

        total = len(stock_analyses)
        insights.append(f"Portfolio sentiment: {buy_count} BUY, {hold_count} HOLD, {sell_count} SELL recommendations")

        # Best and worst performers
        best_stock = max(stock_analyses.values(), key=lambda x: x.score)
        worst_stock = min(stock_analyses.values(), key=lambda x: x.score)

        insights.append(f"Top performer: {best_stock.symbol} ({best_stock.recommendation})")
        insights.append(f"Underperformer: {worst_stock.symbol} ({worst_stock.recommendation})")

        # Risk assessment
        avg_confidence = sum(a.sentiment_score.confidence for a in stock_analyses.values()) / total
        if avg_confidence < 0.5:
            insights.append("Low confidence in sentiment analysis suggests cautious approach")

        return insights

    def _generate_market_summary(self, stock_analyses: Dict[str, StockAnalysis]) -> str:
        """Generate a summary of market conditions affecting the portfolio"""
        if not stock_analyses:
            return "No stocks available for market summary."

        # Calculate average metrics
        avg_change = sum(a.stock_info.change_percent for a in stock_analyses.values()) / len(stock_analyses)
        avg_sentiment = sum(a.sentiment_score.overall_sentiment for a in stock_analyses.values()) / len(stock_analyses)

        # Determine market tone
        if avg_change > 1 and avg_sentiment > 0.2:
            tone = "bullish"
        elif avg_change < -1 and avg_sentiment < -0.2:
            tone = "bearish"
        else:
            tone = "mixed"

        summary = (f"Market conditions appear {tone} for your portfolio. "
                  f"Average price change: {avg_change:+.1f}%, "
                  f"Average X sentiment: {avg_sentiment:+.2f}")

        return summary