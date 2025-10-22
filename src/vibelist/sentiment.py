"""
X sentiment analysis using the xAI API (Grok)
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class SentimentScore(BaseModel):
    """Model for sentiment analysis results"""
    symbol: str
    overall_sentiment: float  # -1.0 (very negative) to 1.0 (very positive)
    sentiment_label: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0.0 to 1.0
    key_insights: List[str]
    post_count: int
    last_updated: datetime
    sources: List[str]


class XaiAPIClient:
    """Client for interacting with the xAI API (Grok) for X sentiment analysis"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"  # Placeholder - actual xAI endpoint may differ
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def analyze_stock_sentiment(self, symbol: str, hours_back: int = 24) -> SentimentScore:
        """
        Analyze X sentiment for a specific stock

        Args:
            symbol: Stock ticker symbol
            hours_back: How many hours back to analyze posts

        Returns:
            SentimentScore object with analysis results
        """
        try:
            symbol = symbol.upper().strip()
            logger.info(f"Analyzing X sentiment for {symbol} over last {hours_back} hours")

            # Construct the prompt for xAI
            prompt = self._build_sentiment_prompt(symbol, hours_back)

            # Make API call to xAI
            response = self._call_xai_api(prompt)

            # Parse and structure the response
            sentiment_score = self._parse_xai_response(response, symbol)

            logger.info(f"Sentiment analysis complete for {symbol}: {sentiment_score.sentiment_label} ({sentiment_score.overall_sentiment:+.2f})")
            return sentiment_score

        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {str(e)}")
            # Return neutral sentiment on error
            return SentimentScore(
                symbol=symbol,
                overall_sentiment=0.0,
                sentiment_label="HOLD",
                confidence=0.0,
                key_insights=[f"Error analyzing sentiment: {str(e)}"],
                post_count=0,
                last_updated=datetime.now(),
                sources=[]
            )

    def _build_sentiment_prompt(self, symbol: str, hours_back: int) -> str:
        """Build the prompt for the xAI API"""

        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        time_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S UTC")

        prompt = f"""
        Analyze X/Twitter sentiment for {symbol} stock from posts since {time_str}.

        Please provide:
        1. Overall sentiment score (-1.0 to 1.0, where -1.0 is very negative, 0 is neutral, 1.0 is very positive)
        2. Recommendation (BUY/SELL/HOLD) based on sentiment
        3. Confidence level (0.0 to 1.0)
        4. Key insights and trends from the posts
        5. Number of posts analyzed
        6. Main sources or influential accounts mentioned

        Focus on recent posts that mention {symbol}, ${symbol}, or the company name.
        Consider both retail investor sentiment and any institutional insights.
        Look for recurring themes, breaking news, or unusual activity.

        Return the analysis in JSON format with this structure:
        {{
            "overall_sentiment": <float>,
            "sentiment_label": "BUY" | "SELL" | "HOLD",
            "confidence": <float>,
            "key_insights": ["<insight 1>", "<insight 2>", ...],
            "post_count": <int>,
            "sources": ["<source 1>", "<source 2>", ...]
        }}
        """

        return prompt

    def _call_xai_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to xAI"""

        try:
            # Note: This is a placeholder implementation
            # The actual xAI API endpoint and parameters may differ
            payload = {
                "model": "grok-beta",  # Placeholder model name
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,  # Lower temperature for more consistent analysis
                "max_tokens": 1000
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"xAI API request failed: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode xAI API response: {str(e)}")
            raise

    def _parse_xai_response(self, response: Dict[str, Any], symbol: str) -> SentimentScore:
        """Parse xAI API response into SentimentScore"""

        try:
            # Extract the content from the response
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
            else:
                raise ValueError("Unexpected response format from xAI API")

            # Try to parse JSON from the content
            # The response might contain markdown code blocks
            if "```json" in content:
                # Extract JSON from markdown code block
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
            else:
                # Try to parse the entire content as JSON
                json_str = content.strip()

            # Parse the JSON
            analysis_data = json.loads(json_str)

            # Validate and create SentimentScore
            return SentimentScore(
                symbol=symbol,
                overall_sentiment=float(analysis_data.get("overall_sentiment", 0.0)),
                sentiment_label=analysis_data.get("sentiment_label", "HOLD"),
                confidence=float(analysis_data.get("confidence", 0.0)),
                key_insights=analysis_data.get("key_insights", []),
                post_count=int(analysis_data.get("post_count", 0)),
                last_updated=datetime.now(),
                sources=analysis_data.get("sources", [])
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse xAI response for {symbol}: {str(e)}")
            logger.debug(f"Raw response: {content if 'content' in locals() else response}")

            # Return neutral sentiment on parsing error
            return SentimentScore(
                symbol=symbol,
                overall_sentiment=0.0,
                sentiment_label="HOLD",
                confidence=0.0,
                key_insights=["Failed to parse sentiment analysis"],
                post_count=0,
                last_updated=datetime.now(),
                sources=[]
            )

    def batch_analyze(self, symbols: List[str], hours_back: int = 24) -> Dict[str, SentimentScore]:
        """
        Analyze sentiment for multiple stocks

        Args:
            symbols: List of stock symbols
            hours_back: Hours to look back for posts

        Returns:
            Dictionary mapping symbols to SentimentScore objects
        """
        results = {}
        errors = []

        for symbol in symbols:
            try:
                sentiment = self.analyze_stock_sentiment(symbol, hours_back)
                results[symbol] = sentiment
            except Exception as e:
                errors.append(f"{symbol}: {str(e)}")
                logger.warning(f"Failed to analyze sentiment for {symbol}: {str(e)}")

        if errors:
            logger.warning(f"Failed to analyze sentiment for some stocks: {'; '.join(errors)}")

        return results
