"""
X sentiment analysis using the xAI API (Grok)
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel

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
    top_quote: Optional[str] = None  # Representative tweet quote
    top_quote_username: Optional[str] = None  # Username of tweet author
    top_quote_tweet_id: Optional[str] = None  # Tweet ID for constructing URL


class XaiAPIClient:
    """Client for interacting with the xAI API (Grok) for X sentiment analysis"""

    def __init__(self, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model or os.getenv("XAI_MODEL", "grok-4-fast")
        self.base_url = base_url or os.getenv("XAI_API_BASE_URL", "https://api.x.ai/v1")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.system_prompt = (
            "You are Grok 4 Fast Reasoning assisting with financial sentiment analysis. "
            "Summarize recent X/Twitter sentiment for the requested stock and respond strictly "
            "with a JSON object matching the provided schema."
        )

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

            # Make API call to xAI with live search
            response = self._call_xai_api(prompt, symbol)

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

        prompt = f"""
        Analyze the X (Twitter) posts about {symbol} stock that were found via live search and provide sentiment analysis.

        Based on the REAL posts found, provide:
        1. Overall sentiment score (-1.0 to 1.0, where -1.0 is very negative, 0 is neutral, 1.0 is very positive)
        2. Recommendation (BUY/SELL/HOLD) based on sentiment
        3. Confidence level (0.0 to 1.0) - higher if more posts found with consistent sentiment
        4. Key insights and trends from the posts
        5. EXACT count of posts you analyzed from the search results
        6. Main sources or influential accounts (usernames without @)
        7. The EXACT TEXT from ONE representative tweet (under 200 chars) that best captures the sentiment
        8. The REAL USERNAME of that tweet author (without @)
        9. The REAL TWEET ID (numeric status ID) from that tweet

        IMPORTANT:
        - Only use data from the actual search results provided
        - If no posts were found, set post_count to 0 and all optional fields to null
        - For the top quote: Choose a tweet with high engagement that represents the overall sentiment
        - Ensure tweet_id and username are from an actual post in the search results

        Return ONLY valid JSON with this structure:
        {{
            "overall_sentiment": <float>,
            "sentiment_label": "BUY" | "SELL" | "HOLD",
            "confidence": <float>,
            "key_insights": ["<insight 1>", "<insight 2>", ...],
            "post_count": <int - actual number of posts analyzed>,
            "sources": ["<username 1>", "<username 2>", ...],
            "top_quote": "<exact tweet text or null if none found>",
            "top_quote_username": "<real username or null>",
            "top_quote_tweet_id": "<real tweet ID or null>"
        }}
        """

        return prompt

    def _call_xai_api(self, prompt: str, symbol: str) -> Dict[str, Any]:
        """Make API call to xAI with live search enabled for real-time X data"""

        try:
            # Build simple search query - Grok will filter by recency via prompt
            # X search syntax (since:, min_faves:) may not work in search_parameters
            search_query = f"{symbol} stock"

            # Add recency instruction to the prompt instead
            cutoff_time = datetime.now() - timedelta(hours=24)
            time_filter = f"Only analyze posts from the last 24 hours (since {cutoff_time.strftime('%Y-%m-%d %H:%M UTC')}). Ignore any posts older than 24 hours."
            prompt_with_filter = f"{time_filter}\n\n{prompt.strip()}"

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt_with_filter,
                    },
                ],
                "temperature": 0.2,
                "max_tokens": 1200,
                "response_format": {"type": "json_object"},
                "search_parameters": {
                    "query": search_query,
                    "num_sources": 10
                }
            }

            logger.info(f"Sending API request with live search enabled for {symbol}")
            logger.info(f"Search query: {search_query}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60,
            )

            response.raise_for_status()
            response_data = response.json()

            # Log raw response for debugging
            logger.info(f"Raw API response received")
            logger.debug(f"Full response: {json.dumps(response_data, indent=2)}")

            return response_data

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            logger.error(
                "xAI API request failed with status %s: %s. Verify your Grok model access, "
                "API base URL, and that the `grok-4-fast` model identifier is correct.",
                status,
                e,
            )
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"xAI API request failed: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode xAI API response: {str(e)}")
            raise

    def _parse_xai_response(self, response: Dict[str, Any], symbol: str) -> SentimentScore:
        """Parse xAI API response into SentimentScore"""

        try:
            content = ""
            citations = []

            # Extract citations from response (real tweet URLs from live search)
            if "citations" in response:
                citations = response["citations"]
                logger.info(f"Found {len(citations)} citations for {symbol}")
                logger.debug(f"Citations: {citations[:5]}")  # Log first 5

            # Extract the content from the response
            if "choices" in response and len(response["choices"]) > 0:
                message = response["choices"][0]["message"]
                content = message.get("content", "")

                logger.debug(f"Message content type: {type(content)}")
                logger.debug(f"Message keys: {message.keys()}")

                # Check for tool calls (indicates search was used)
                if message.get("tool_calls"):
                    logger.info(f"Tool calls detected in response for {symbol}")
                    logger.debug(f"Tool calls: {json.dumps(message.get('tool_calls'), indent=2)}")
                    for tool_call in message["tool_calls"]:
                        arguments = (
                            tool_call.get("function", {}).get("arguments")
                            if isinstance(tool_call, dict)
                            else None
                        )
                        if arguments:
                            content = arguments
                            logger.info(f"Using tool call arguments as content")
                            break

                if isinstance(content, list):
                    text_chunks = [
                        chunk.get("text", "")
                        for chunk in content
                        if isinstance(chunk, dict) and chunk.get("type") == "text"
                    ]
                    content = "\n".join(filter(None, text_chunks))

            else:
                raise ValueError("Unexpected response format from xAI API")

            logger.debug(f"Raw content before JSON parsing: {content[:500]}...")

            # Try to parse JSON from the content
            # The response might contain markdown code blocks
            if "```json" in content:
                # Extract JSON from markdown code block
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
                logger.debug(f"Extracted JSON from markdown block")
            else:
                # Try to parse the entire content as JSON
                json_str = content.strip()

            # Parse the JSON
            analysis_data = json.loads(json_str)
            logger.info(f"Successfully parsed JSON for {symbol}")

            # Parse citation URLs to extract real tweet data
            # Filter citations to find recent tweets (Twitter Snowflake IDs encode timestamp)
            citation_username = None
            citation_tweet_id = None

            def is_tweet_recent(tweet_id_str: str, hours: int = 168) -> bool:
                """Check if tweet ID is from last N hours (default 7 days) using Snowflake ID"""
                try:
                    # Twitter Snowflake ID format: first 41 bits are milliseconds since Twitter epoch (2010-11-04)
                    tweet_id = int(tweet_id_str)
                    twitter_epoch = 1288834974657  # Nov 4, 2010 in ms
                    timestamp_ms = (tweet_id >> 22) + twitter_epoch
                    tweet_time = datetime.fromtimestamp(timestamp_ms / 1000)
                    age_hours = (datetime.now() - tweet_time).total_seconds() / 3600
                    return age_hours <= hours
                except:
                    return True  # If we can't parse, assume it's valid

            if citations and len(citations) > 0:
                # Find first recent citation
                import re
                for citation in citations[:5]:  # Check first 5 citations
                    match = re.search(r'x\.com/([^/]+)/status/(\d+)', citation)
                    if match:
                        username = match.group(1)
                        tweet_id = match.group(2)

                        # Check if tweet is recent (within last week)
                        if is_tweet_recent(tweet_id, hours=168):
                            citation_username = username
                            citation_tweet_id = tweet_id
                            logger.info(f"Parsed citation: @{citation_username}/status/{citation_tweet_id} (recent)")
                            break
                        else:
                            logger.debug(f"Skipping old tweet: @{username}/status/{tweet_id}")

                if not citation_username:
                    logger.warning(f"No recent tweets found in citations for {symbol}, using first citation anyway")
                    match = re.search(r'x\.com/([^/]+)/status/(\d+)', citations[0])
                    if match:
                        citation_username = match.group(1)
                        citation_tweet_id = match.group(2)

            # Validate and create SentimentScore
            # Use citation data if available, fall back to analysis_data
            tweet_id = citation_tweet_id or analysis_data.get("top_quote_tweet_id")
            username = citation_username or analysis_data.get("top_quote_username")

            # Convert tweet ID to string if it's a number
            if tweet_id is not None:
                tweet_id = str(tweet_id)

            return SentimentScore(
                symbol=symbol,
                overall_sentiment=float(analysis_data.get("overall_sentiment", 0.0)),
                sentiment_label=analysis_data.get("sentiment_label", "HOLD"),
                confidence=float(analysis_data.get("confidence", 0.0)),
                key_insights=analysis_data.get("key_insights", []),
                post_count=int(analysis_data.get("post_count", 0)),
                last_updated=datetime.now(),
                sources=analysis_data.get("sources", []),
                top_quote=analysis_data.get("top_quote"),
                top_quote_username=username,
                top_quote_tweet_id=tweet_id
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
